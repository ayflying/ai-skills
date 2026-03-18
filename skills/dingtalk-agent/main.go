package main

import (
	"bufio"
	"context"
	"encoding/json"
	"fmt"
	"os"
	"os/exec"
	"regexp"
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
	TimeoutDuration   = 1 * time.Hour
	CurrentModel      = "opencode/minimax-m2.5-free"
	SessionsFile      = "sessions.json"       // 用户模式开关文件
	GroupContextsFile = "group_contexts.json" // 群组共享上下文文件
)

// 用户会话状态 (仅存储模式开关)
type UserSession struct {
	IsInOpenCodeMode bool      `json:"is_in_opencode_mode"`
	LastActiveTime   time.Time `json:"last_active_time"`
}

var (
	// 用户模式开关: map[UserId]UserSession
	userSessions   = make(map[string]*UserSession)
	userSessionsMu sync.RWMutex

	// 群组共享上下文: map[ConversationId]OpenCodeSessionID
	groupContexts   = make(map[string]string)
	groupContextsMu sync.RWMutex

	// 消息去重
	processedMsgs sync.Map
)

// --- 持久化逻辑 ---

func saveUserSessions() {
	userSessionsMu.RLock()
	defer userSessionsMu.RUnlock()
	data, err := json.MarshalIndent(userSessions, "", "  ")
	if err != nil {
		logToFile(fmt.Sprintf("ERROR: Failed to marshal user sessions: %v", err))
		return
	}
	if err := os.WriteFile(SessionsFile, data, 0644); err != nil {
		logToFile(fmt.Sprintf("ERROR: Failed to write user sessions file: %v", err))
	}
}

func loadUserSessions() {
	userSessionsMu.Lock()
	defer userSessionsMu.Unlock()
	data, err := os.ReadFile(SessionsFile)
	if err != nil {
		if !os.IsNotExist(err) {
			logToFile(fmt.Sprintf("ERROR: Failed to read user sessions file: %v", err))
		}
		return
	}
	if err := json.Unmarshal(data, &userSessions); err != nil {
		logToFile(fmt.Sprintf("ERROR: Failed to unmarshal user sessions: %v", err))
	}
	logToFile(fmt.Sprintf("DEBUG: Loaded %d user sessions", len(userSessions)))
}

func saveGroupContexts() {
	groupContextsMu.RLock()
	defer groupContextsMu.RUnlock()
	data, err := json.MarshalIndent(groupContexts, "", "  ")
	if err != nil {
		logToFile(fmt.Sprintf("ERROR: Failed to marshal group contexts: %v", err))
		return
	}
	if err := os.WriteFile(GroupContextsFile, data, 0644); err != nil {
		logToFile(fmt.Sprintf("ERROR: Failed to write group contexts file: %v", err))
	}
}

func loadGroupContexts() {
	groupContextsMu.Lock()
	defer groupContextsMu.Unlock()
	data, err := os.ReadFile(GroupContextsFile)
	if err != nil {
		if !os.IsNotExist(err) {
			logToFile(fmt.Sprintf("ERROR: Failed to read group contexts file: %v", err))
		}
		return
	}
	if err := json.Unmarshal(data, &groupContexts); err != nil {
		logToFile(fmt.Sprintf("ERROR: Failed to unmarshal group contexts: %v", err))
	}
	logToFile(fmt.Sprintf("DEBUG: Loaded %d group contexts", len(groupContexts)))
}

func logToFile(msg string) {
	f, err := os.OpenFile("chat.log", os.O_APPEND|os.O_CREATE|os.O_WRONLY, 0644)
	if err != nil {
		return
	}
	defer f.Close()
	f.WriteString(fmt.Sprintf("%s %s\n", time.Now().Format("15:04:05"), msg))
}

// --- 会话管理 ---

func getUserSession(userKey string) *UserSession {
	userSessionsMu.Lock()
	defer userSessionsMu.Unlock()
	if session, exists := userSessions[userKey]; exists {
		return session
	}
	session := &UserSession{
		IsInOpenCodeMode: false,
		LastActiveTime:   time.Now(),
	}
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
		go saveUserSessions()
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

// --- OpenCode 交互 ---

func sendMarkdown(ctx context.Context, sessionWebhook, title, text string) error {
	replier := chatbot.NewChatbotReplier()
	err := replier.SimpleReplyMarkdown(ctx, sessionWebhook, []byte(title), []byte(text))
	if err != nil {
		logToFile(fmt.Sprintf("ERROR: sendMarkdown failed: %v", err))
	}
	return err
}

func callOpenCode(ctx context.Context, sessionWebhook string, prompt string, groupSessionID *string) error {
	logToFile(fmt.Sprintf("DEBUG: callOpenCode started for prompt: %s, groupSessionID: %s", prompt, *groupSessionID))

	opencodePath := `D:\Users\ay\AppData\Local\OpenCode\opencode-cli.exe`
	args := []string{"run", "--attach", "http://127.0.0.1:9090", "--model", CurrentModel, "--format", "json"}

	if *groupSessionID != "" {
		args = append(args, "-s", *groupSessionID)
	}

	args = append(args, prompt)
	cmd := exec.Command(opencodePath, args...)
	cmd.Env = os.Environ()

	stdout, err := cmd.StdoutPipe()
	if err != nil {
		return fmt.Errorf("无法获取标准输出管道: %v", err)
	}
	stderr, err := cmd.StderrPipe()
	if err != nil {
		return fmt.Errorf("无法获取标准错误管道: %v", err)
	}

	if err := cmd.Start(); err != nil {
		return fmt.Errorf("启动命令失败: %v", err)
	}

	var currentMessage string
	sessionIDMu := sync.Mutex{}
	done := make(chan bool)

	go func() {
		scanner := bufio.NewScanner(stdout)
		for scanner.Scan() {
			line := scanner.Text()
			if strings.TrimSpace(line) == "" {
				continue
			}

			var event struct {
				Type      string `json:"type"`
				SessionID string `json:"sessionID"`
				Part      struct {
					Text string `json:"text"`
					Type string `json:"type"`
				} `json:"part"`
			}

			if err := json.Unmarshal([]byte(line), &event); err != nil {
				continue
			}

			if event.SessionID != "" {
				sessionIDMu.Lock()
				if *groupSessionID == "" {
					*groupSessionID = event.SessionID
					logToFile(fmt.Sprintf("DEBUG: New group sessionID captured: %s", *groupSessionID))
					go saveGroupContexts()
				}
				sessionIDMu.Unlock()
			}

			if event.Type == "text" && event.Part.Text != "" {
				currentMessage += event.Part.Text
				if len(currentMessage) > 800 || strings.HasSuffix(currentMessage, "\n") {
					markdownContent := convertToMarkdown(currentMessage)
					sendMarkdown(ctx, sessionWebhook, "OpenCode 结果", markdownContent)
					currentMessage = ""
				}
			} else if event.Type == "tool_use" {
				var toolEvent struct {
					Part struct {
						State struct {
							Output string `json:"output"`
							Title  string `json:"title"`
						} `json:"state"`
					} `json:"part"`
				}
				if err := json.Unmarshal([]byte(line), &toolEvent); err == nil {
					if toolEvent.Part.State.Output != "" {
						toolOutput := fmt.Sprintf("### 🔧 工具执行: %s\n\n```\n%s\n```",
							toolEvent.Part.State.Title,
							truncateOutput(toolEvent.Part.State.Output))
						sendMarkdown(ctx, sessionWebhook, "工具执行", toolOutput)
					}
				}
			}
		}

		if currentMessage != "" {
			markdownContent := convertToMarkdown(currentMessage)
			sendMarkdown(ctx, sessionWebhook, "执行结果", markdownContent)
			currentMessage = ""
		}
		done <- true
	}()

	go func() {
		stderrScanner := bufio.NewScanner(stderr)
		for stderrScanner.Scan() {
			line := stderrScanner.Text()
			logToFile(fmt.Sprintf("STDERR: %s", line))
		}
	}()

	<-done
	if err := cmd.Wait(); err != nil {
		return fmt.Errorf("命令执行失败: %v", err)
	}
	return nil
}

func convertToMarkdown(text string) string {
	codeBlockRegex := regexp.MustCompile("```(\\w+)?\\n([\\s\\S]*?)```")
	if codeBlockRegex.MatchString(text) {
		return text
	}

	lines := strings.Split(text, "\n")
	var hasCode bool
	for _, line := range lines {
		if strings.HasPrefix(line, "    ") || strings.HasPrefix(line, "\t") {
			hasCode = true
			break
		}
	}

	if hasCode {
		return "```\n" + text + "\n```"
	}
	return text
}

func truncateOutput(output string) string {
	maxLen := 1500
	if len(output) <= maxLen {
		return output
	}
	return output[:maxLen] + "\n... (输出过长已截断)"
}

// --- 消息处理 ---

func OnChatBotMessageReceived(ctx context.Context, data *chatbot.BotCallbackDataModel) ([]byte, error) {
	// 增加调试日志：确认回调被触发
	logToFile("DEBUG: OnChatBotMessageReceived callback triggered!")

	// 消息去重
	msgID := data.MsgId
	if msgID != "" {
		if _, loaded := processedMsgs.LoadOrStore(msgID, time.Now()); loaded {
			logToFile(fmt.Sprintf("DEBUG: Duplicate message received, skipping: %s", msgID))
			return []byte(""), nil
		}
	}

	content := strings.TrimSpace(data.Text.Content)
	senderNick := data.SenderNick

	// 1. 确定用户 Key (用于独立控制模式)
	userKey := data.SenderStaffId
	if userKey == "" {
		userKey = data.SenderId
	}
	if userKey == "" {
		userKey = senderNick
	}

	// 2. 确定群组 Key (用于共享上下文)
	groupKey := data.ConversationId
	if groupKey == "" {
		groupKey = userKey // 私聊 fallback
	}

	logToFile(fmt.Sprintf("收到原始: '%s' (用户: %s, 群组: %s)", content, userKey, groupKey))
	logToFile(fmt.Sprintf("DEBUG: ConversationType: %s, SenderId: %s", data.ConversationType, data.SenderId))

	// 清理过期会话
	cleanupExpiredSessions()

	// 获取用户模式状态
	userSession := getUserSession(userKey)
	userSession.LastActiveTime = time.Now()
	go saveUserSessions()

	// 获取群组共享的 OpenCode SessionID
	groupContextsMu.Lock()
	groupSessionID, exists := groupContexts[groupKey]
	if !exists {
		groupSessionID = ""
	}
	groupContextsMu.Unlock()

	// 处理命令
	if strings.HasPrefix(content, "/") {
		parts := strings.SplitN(content, " ", 2)
		cmd := parts[0]
		switch cmd {
		case "/help":
			reply := "可用命令:\n/help\n/opencode <任务> - 进入OpenCode模式\n/exit - 退出OpenCode模式\n/status - 查看状态"
			chatbotReplier := chatbot.NewChatbotReplier()
			chatbotReplier.SimpleReplyText(ctx, data.SessionWebhook, []byte(reply))
			return []byte(""), nil
		case "/status":
			modeStatus := "普通模式"
			if userSession.IsInOpenCodeMode {
				modeStatus = "OpenCode模式"
			}
			reply := fmt.Sprintf("Agent运行中\n当前模式: %s\n群组ID: %s", modeStatus, groupKey)
			chatbotReplier := chatbot.NewChatbotReplier()
			chatbotReplier.SimpleReplyText(ctx, data.SessionWebhook, []byte(reply))
			return []byte(""), nil
		case "/opencode":
			userSession.IsInOpenCodeMode = true
			go saveUserSessions()
			if len(parts) > 1 {
				modelInfo := fmt.Sprintf("### 🤖 已进入OpenCode模式\n\n- **当前模型**: `%s`\n- **群组**: `%s`\n\n开始执行任务...", CurrentModel, groupKey)
				sendMarkdown(ctx, data.SessionWebhook, "进入OpenCode模式", modelInfo)

				// 在协程中执行任务
				go func() {
					// 注意：这里传递的是 groupSessionID 的指针，callOpenCode 会更新它
					err := callOpenCode(ctx, data.SessionWebhook, parts[1], &groupSessionID)
					if err != nil {
						logToFile(fmt.Sprintf("OpenCode执行错误: %v", err))
						chatbotReplier := chatbot.NewChatbotReplier()
						chatbotReplier.SimpleReplyText(ctx, data.SessionWebhook, []byte(fmt.Sprintf("执行失败: %v", err)))
					}
					// 更新群组上下文并保存
					groupContextsMu.Lock()
					groupContexts[groupKey] = groupSessionID
					groupContextsMu.Unlock()
					saveGroupContexts()
				}()
				return []byte(""), nil
			} else {
				modelInfo := fmt.Sprintf("### 🤖 已进入OpenCode模式\n\n- **当前模型**: `%s`\n- **群组**: `%s`\n\n请输入任务（或发送 `/exit` 退出）", CurrentModel, groupKey)
				sendMarkdown(ctx, data.SessionWebhook, "进入OpenCode模式", modelInfo)
				return []byte(""), nil
			}
		case "/exit":
			userSession.IsInOpenCodeMode = false
			go saveUserSessions()
			chatbotReplier := chatbot.NewChatbotReplier()
			chatbotReplier.SimpleReplyText(ctx, data.SessionWebhook, []byte("已退出OpenCode模式"))
			return []byte(""), nil
		default:
			chatbotReplier := chatbot.NewChatbotReplier()
			chatbotReplier.SimpleReplyText(ctx, data.SessionWebhook, []byte(fmt.Sprintf("未知命令: %s\n输入 /help 查看帮助", cmd)))
			return []byte(""), nil
		}
	} else {
		// 非命令消息
		if userSession.IsInOpenCodeMode {
			sendMarkdown(ctx, data.SessionWebhook, "任务执行", "### 🤖 开始执行任务...")

			// 在协程中执行任务
			go func() {
				err := callOpenCode(ctx, data.SessionWebhook, content, &groupSessionID)
				if err != nil {
					logToFile(fmt.Sprintf("OpenCode执行错误: %v", err))
					chatbotReplier := chatbot.NewChatbotReplier()
					chatbotReplier.SimpleReplyText(ctx, data.SessionWebhook, []byte(fmt.Sprintf("执行失败: %v", err)))
				}
				// 更新群组上下文并保存
				groupContextsMu.Lock()
				groupContexts[groupKey] = groupSessionID
				groupContextsMu.Unlock()
				saveGroupContexts()
			}()
			return []byte(""), nil
		} else {
			chatbotReplier := chatbot.NewChatbotReplier()
			chatbotReplier.SimpleReplyText(ctx, data.SessionWebhook, []byte("我收到了: "+content))
			return []byte(""), nil
		}
	}
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
	fmt.Printf(format+"\n", args...)
}
func (l *simpleLogger) Fatalf(format string, args ...interface{}) {
	logToFile(fmt.Sprintf("FATAL: "+format, args...))
	fmt.Printf(format+"\n", args...)
}

func main() {
	// 清空旧日志，方便调试
	f, _ := os.Create("chat.log")
	f.Close()

	logger.SetLogger(&simpleLogger{})

	// 加载持久化数据
	loadUserSessions()
	loadGroupContexts()

	// 重启时清空去重记录，避免误判旧消息为重复
	processedMsgs = sync.Map{}

	// 启动消息去重清理任务
	go cleanupProcessedMsgs()

	// 创建客户端
	cli := client.NewStreamClient(client.WithAppCredential(client.NewAppCredentialConfig(ClientID, ClientSecret)))

	// 注册聊天机器人回调
	cli.RegisterChatBotCallbackRouter(OnChatBotMessageReceived)

	fmt.Println("Agent started")
	logToFile("Agent started")

	// 错误处理：确保程序不会静默退出
	err := cli.Start(context.Background())
	if err != nil {
		logToFile(fmt.Sprintf("连接失败: %v", err))
		fmt.Printf("连接失败: %v\n", err)
		return
	}

	logToFile("连接成功")
	fmt.Println("连接成功")

	defer cli.Close()
	select {}
}
