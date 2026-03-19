package main

import (
	"bufio"
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"os"
	"os/exec"
	"strings"
	"sync"
	"time"

	"github.com/open-dingtalk/dingtalk-stream-sdk-go/chatbot"
	"github.com/open-dingtalk/dingtalk-stream-sdk-go/client"
	"github.com/open-dingtalk/dingtalk-stream-sdk-go/logger"
)

const (
	ClientID          = "dingdyjw7dykkua9x0he"
	ClientSecret      = "_IPx3Em72K6os2nQiFq6O4VGSEUcjJu-hlZihSnI5oawj1xI1WB_DP-5ZXjXykRq"
	TimeoutDuration   = 10 * time.Minute
	SessionsFile      = "sessions.json"
	GroupContextsFile = "group_contexts.json"
	// opencode-api 技能路径
	OpencodeScriptPath = `D:\git\yunloli\game2\.agents\skills\opencode-api\scripts\opencode_runner.py`
)

type UserSession struct {
	IsInOpenCodeMode bool      `json:"is_in_opencode_mode"`
	LastActiveTime   time.Time `json:"last_active_time"`
}

var (
	userSessions    = make(map[string]*UserSession)
	userSessionsMu  sync.RWMutex
	groupContexts   = make(map[string]string)
	groupContextsMu sync.RWMutex
	processedMsgs   sync.Map
)

func saveUserSessionsSync() {
	userSessionsMu.RLock()
	defer userSessionsMu.RUnlock()
	data, _ := json.MarshalIndent(userSessions, "", "  ")
	os.WriteFile(SessionsFile, data, 0644)
}

func saveUserSessions() { saveUserSessionsSync() }

func loadUserSessions() {
	userSessionsMu.Lock()
	defer userSessionsMu.Unlock()
	data, err := os.ReadFile(SessionsFile)
	if err == nil {
		json.Unmarshal(data, &userSessions)
	}
}

func saveGroupContexts() {
	groupContextsMu.RLock()
	defer groupContextsMu.RUnlock()
	data, _ := json.MarshalIndent(groupContexts, "", "  ")
	os.WriteFile(GroupContextsFile, data, 0644)
}

func loadGroupContexts() {
	groupContextsMu.Lock()
	defer groupContextsMu.Unlock()
	data, err := os.ReadFile(GroupContextsFile)
	if err == nil {
		json.Unmarshal(data, &groupContexts)
	}
}

func logToFile(msg string) {
	f, _ := os.OpenFile("chat.log", os.O_APPEND|os.O_CREATE|os.O_WRONLY, 0644)
	if f != nil {
		defer f.Close()
		f.WriteString(fmt.Sprintf("%s %s\n", time.Now().Format("15:04:05"), msg))
	}
}

func getUserSession(userKey string) *UserSession {
	userSessionsMu.Lock()
	defer userSessionsMu.Unlock()
	if session, exists := userSessions[userKey]; exists {
		return session
	}
	session := &UserSession{IsInOpenCodeMode: false, LastActiveTime: time.Now()}
	userSessions[userKey] = session
	return session
}

func cleanupExpiredSessions() {
	userSessionsMu.Lock()
	defer userSessionsMu.Unlock()
	now := time.Now()
	modified := false
	for _, session := range userSessions {
		if now.Sub(session.LastActiveTime) > TimeoutDuration && session.IsInOpenCodeMode {
			session.IsInOpenCodeMode = false
			modified = true
		}
	}
	if modified {
		saveUserSessionsSync()
	}
}

func cleanupProcessedMsgs() {
	for {
		time.Sleep(10 * time.Minute)
		now := time.Now()
		processedMsgs.Range(func(key, value interface{}) bool {
			if t, ok := value.(time.Time); ok && now.Sub(t) > 10*time.Minute {
				processedMsgs.Delete(key)
			}
			return true
		})
	}
}

func sendMarkdown(ctx context.Context, sessionWebhook, title, text string) error {
	replier := chatbot.NewChatbotReplier()
	return replier.SimpleReplyMarkdown(ctx, sessionWebhook, []byte(title), []byte(text))
}

// 调用 opencode-api 技能执行任务
func callOpenCodeAPI(ctx context.Context, sessionWebhook string, prompt string, chatTitle string) error {
	logToFile(fmt.Sprintf("DEBUG: callOpenCodeAPI started, prompt: %s, title: %s", prompt, chatTitle))

	args := []string{OpencodeScriptPath, prompt, "--json"}

	cmd := exec.Command("python", args...)
	cmd.Env = os.Environ()

	stdout, err := cmd.StdoutPipe()
	if err != nil {
		logToFile(fmt.Sprintf("ERROR: stdout pipe failed: %v", err))
		return err
	}

	if err := cmd.Start(); err != nil {
		logToFile(fmt.Sprintf("ERROR: command start failed: %v", err))
		return err
	}

	// 读取输出
	scanner := bufio.NewScanner(stdout)
	var output strings.Builder
	for scanner.Scan() {
		output.WriteString(scanner.Text() + "\n")
	}

	cmd.Wait()

	// 解析 JSON 结果
	var result map[string]interface{}
	if err := json.Unmarshal([]byte(output.String()), &result); err != nil {
		logToFile(fmt.Sprintf("ERROR: json unmarshal failed: %v, output: %s", err, output.String()))
		// 如果不是 JSON，直接发送原始输出
		if output.Len() > 0 {
			sendMarkdown(ctx, sessionWebhook, "OpenCode 结果", output.String())
		}
		return nil
	}

	// 检查执行结果
	if success, ok := result["success"].(bool); ok && success {
		if outputStr, ok := result["output"].(string); ok && outputStr != "" {
			sendMarkdown(ctx, sessionWebhook, "OpenCode 结果", outputStr)
		}
	} else {
		errorMsg := "执行失败"
		if errStr, ok := result["error"].(string); ok {
			errorMsg = errStr
		}
		sendMarkdown(ctx, sessionWebhook, "执行失败", errorMsg)
	}

	return nil
}

func OnChatBotMessageReceived(ctx context.Context, data *chatbot.BotCallbackDataModel) ([]byte, error) {
	msgID := data.MsgId
	if msgID != "" {
		if _, loaded := processedMsgs.LoadOrStore(msgID, time.Now()); loaded {
			return []byte(""), nil
		}
	}

	content := strings.TrimSpace(data.Text.Content)
	senderNick := data.SenderNick
	userKey := data.SenderStaffId
	if userKey == "" {
		userKey = data.SenderId
	}
	groupKey := data.ConversationId
	if groupKey == "" {
		groupKey = userKey
	}

	// 确定标题：使用 ID 后8位确保唯一性
	shortUserKey := userKey
	if len(userKey) > 8 {
		shortUserKey = userKey[len(userKey)-8:]
	}
	chatTitle := fmt.Sprintf("%s-%s", senderNick, shortUserKey)
	if data.ConversationType == "2" {
		shortGroupKey := groupKey
		if len(groupKey) > 8 {
			shortGroupKey = groupKey[len(groupKey)-8:]
		}
		chatTitle = fmt.Sprintf("群聊-%s", shortGroupKey)
	}

	logToFile(fmt.Sprintf("收到: '%s' (用户: %s, 标题: %s)", content, userKey, chatTitle))

	userSession := getUserSession(userKey)
	userSession.LastActiveTime = time.Now()
	cleanupExpiredSessions()

	if strings.HasPrefix(content, "/") {
		parts := strings.SplitN(content, " ", 2)
		switch parts[0] {
		case "/help":
			reply := "可用命令:\n/help\n/opencode <任务>\n/jimeng <提示词>\n/exit\n/status"
			chatbot.NewChatbotReplier().SimpleReplyText(ctx, data.SessionWebhook, []byte(reply))
		case "/jimeng":
			if len(parts) > 1 {
				go func(p, tid, hook string) {
					taskData := map[string]string{"id": tid, "prompt": p}
					jsonData, _ := json.Marshal(taskData)
					http.Post("http://127.0.0.1:18542/add_task", "application/json", bytes.NewBuffer(jsonData))
					sendMarkdown(ctx, hook, "任务排队", "✅ 任务已排队，正在生成...")
				}(parts[1], fmt.Sprintf("dt_%d", time.Now().Unix()), data.SessionWebhook)
			}
		case "/status":
			status := "普通模式"
			if userSession.IsInOpenCodeMode {
				status = "专注模式"
			}
			reply := fmt.Sprintf("当前模式: %s\n会话: %s", status, chatTitle)
			chatbot.NewChatbotReplier().SimpleReplyText(ctx, data.SessionWebhook, []byte(reply))
		case "/opencode":
			userSession.IsInOpenCodeMode = true
			saveUserSessionsSync()
			sendMarkdown(ctx, data.SessionWebhook, "专注模式", "### 🤖 已进入专注模式\n\n会话: "+chatTitle)
		case "/exit":
			userSession.IsInOpenCodeMode = false
			saveUserSessionsSync()
			chatbot.NewChatbotReplier().SimpleReplyText(ctx, data.SessionWebhook, []byte("已退出专注模式"))
		}
		return []byte(""), nil
	}

	if !userSession.IsInOpenCodeMode {
		userSession.IsInOpenCodeMode = true
		saveUserSessionsSync()
		sendMarkdown(ctx, data.SessionWebhook, "专注模式", "### 🤖 已自动进入专注模式 ("+chatTitle+")\n\n发送 `/exit` 退出。")
	}

	if userSession.IsInOpenCodeMode {
		sendMarkdown(ctx, data.SessionWebhook, "任务执行", "### 🤖 开始执行...")
		go func() {
			err := callOpenCodeAPI(ctx, data.SessionWebhook, content, chatTitle)
			if err != nil {
				logToFile(fmt.Sprintf("ERROR: callOpenCodeAPI failed: %v", err))
				sendMarkdown(ctx, data.SessionWebhook, "错误", fmt.Sprintf("执行失败: %v", err))
			}
		}()
	}
	return []byte(""), nil
}

type simpleLogger struct{}

func (l *simpleLogger) Debugf(format string, args ...interface{}) {
	logToFile(fmt.Sprintf("DEBUG: "+format, args...))
}
func (l *simpleLogger) Infof(format string, args ...interface{}) {
	logToFile(fmt.Sprintf("INFO: "+format, args...))
}
func (l *simpleLogger) Warningf(format string, args ...interface{}) {
	logToFile(fmt.Sprintf("WARNING: "+format, args...))
}
func (l *simpleLogger) Errorf(format string, args ...interface{}) {
	logToFile(fmt.Sprintf("ERROR: "+format, args...))
}
func (l *simpleLogger) Fatalf(format string, args ...interface{}) {
	logToFile(fmt.Sprintf("FATAL: "+format, args...))
}

func main() {
	f, _ := os.Create("chat.log")
	f.Close()
	logger.SetLogger(&simpleLogger{})
	loadUserSessions()
	loadGroupContexts()
	go cleanupProcessedMsgs()

	cli := client.NewStreamClient(client.WithAppCredential(client.NewAppCredentialConfig(ClientID, ClientSecret)))
	cli.RegisterChatBotCallbackRouter(OnChatBotMessageReceived)
	err := cli.Start(context.Background())
	if err != nil {
		fmt.Printf("启动失败: %v\n", err)
		return
	}
	select {}
}
