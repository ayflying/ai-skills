package main

import (
	"context"
	"fmt"
	"os"
	"strings"
	"testing"

	"github.com/open-dingtalk/dingtalk-stream-sdk-go/chatbot"
)

func TestParseCommand(t *testing.T) {
	testCases := []struct {
		input    string
		expected string
	}{
		{"  /help  ", "/help"},
		{" /status ", "/status"},
		{" /opencode hello", "/opencode hello"},
		{" 你好", "normal"},
	}

	for _, tc := range testCases {
		content := strings.TrimSpace(tc.input)
		if !strings.HasPrefix(content, "/") && strings.HasPrefix(strings.TrimLeft(tc.input, " "), "/") {
			content = tc.input[strings.Index(tc.input, "/"):]
		}
		if strings.HasPrefix(content, "/") {
			if content != tc.expected {
				t.Errorf("输入 '%s': 期望 '%s', 得到 '%s'", tc.input, tc.expected, content)
			}
		} else {
			if "normal" != tc.expected {
				t.Errorf("输入 '%s': 期望普通消息, 得到 '%s'", tc.input, content)
			}
		}
	}
}

func TestOnChatBotMessageReceived(t *testing.T) {
	// 初始化日志文件
	f, _ := os.Create("chat.log")
	f.Close()

	data := &chatbot.BotCallbackDataModel{
		Text: chatbot.BotCallbackDataTextModel{
			Content: "  /help  ",
		},
		SessionWebhook: "test-webhook",
		SenderId:       "test-sender-id",
		ConversationId: "test-conversation-id",
	}

	// 调用处理函数
	ctx := context.Background()
	result, err := OnChatBotMessageReceived(ctx, data)
	if err != nil {
		t.Errorf("处理消息失败: %v", err)
	}

	// 检查返回值
	// 钉钉机器人通过 SessionWebhook 发送消息，返回空字节数组是正常的
	if len(result) != 0 {
		t.Error("期望返回空字节数组")
	}

	// 检查日志
	content, _ := os.ReadFile("chat.log")
	fmt.Printf("日志内容:\n%s\n", string(content))
}
