// content.js - 跨标签锁定稳健版 (版本: 1.16)
const VERSION = "1.16";
const SERVER_URL = 'http://localhost:18542';
const TAB_ID = Math.random().toString(36).substring(7);

console.log(`[助手 v${VERSION}] 标签页 ID: ${TAB_ID} 已启动`);

let isProcessingTask = false;
let lastTaskTime = 0; // 上次任务完成时间

// 跨标签页抢锁逻辑：确保只有一个标签页在工作
function tryGetMasterLock() {
    const lockKey = 'jimeng_master_lock';
    const now = Date.now();
    const lockData = JSON.parse(localStorage.getItem(lockKey) || '{}');

    // 如果锁不存在，或者锁已过期（超过 10 秒），则抢锁
    if (!lockData.id || (now - lockData.ts > 10000) || lockData.id === TAB_ID) {
        localStorage.setItem(lockKey, JSON.stringify({ id: TAB_ID, ts: now }));
        return true;
    }
    return false;
}

// 下载生成的图片
async function downloadGeneratedImage(taskId) {
    try {
        // 等待图片加载
        await new Promise(r => setTimeout(r, 2000));
        
        // 查找生成的图片元素 (即梦AI的图片通常在特定的容器中)
        const images = document.querySelectorAll('img[src*="jianying"], img[src*="seaway"]');
        if (images.length > 0) {
            const img = images[0];
            const imgUrl = img.src;
            
            // 发送图片URL到服务器保存
            await fetch(`${SERVER_URL}/save_image`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    taskId: taskId, 
                    url: imgUrl,
                    timestamp: Date.now()
                })
            });
            console.log(`>>> [图片已保存] ${imgUrl.substring(0, 50)}...`);
        } else {
            // 尝试查找下载按钮
            const downloadBtn = Array.from(document.querySelectorAll('button, span')).find(el => 
                (el.innerText || '').includes('下载') || (el.innerText || '').includes('保存')
            );
            if (downloadBtn) {
                downloadBtn.click();
                console.log(">>> [点击下载按钮]");
            }
        }
    } catch (e) {
        console.error(">>> [下载失败]", e);
    }
}

async function heartbeat() {
    // 任务完成后至少等待10秒冷却期，防止重复提交
    if (isProcessingTask || (Date.now() - lastTaskTime < 10000)) return;
    
    // 1. 只有拿到了 Master 锁的标签页才允许通信
    if (!tryGetMasterLock()) {
        // console.log("其他标签页正在工作，本页待命...");
        return;
    }

    // 2. 检查 UI 就绪
    const editor = document.querySelector('[contenteditable="true"]');
    if (!editor || !window.location.href.includes('generate')) return;

    try {
        const response = await fetch(`${SERVER_URL}/get_task?v=${VERSION}`);
        const task = await response.json();
        
        if (task.id) {
            console.log(`>>> [抢单成功] 正在处理 ID: ${task.id}`);
            isProcessingTask = true;
            await doTask(editor, task);
            isProcessingTask = false;
        }
    } catch (e) {
        // 连接失败时静默，不刷屏
    }
}

async function doTask(editor, task) {
    try {
        // 1. 模型切换
        const v4Btn = Array.from(document.querySelectorAll('button, span, div')).find(el => 
            (el.innerText || el.textContent || "").includes('4.0')
        );
        if (v4Btn) { v4Btn.click(); await new Promise(r => setTimeout(r, 1000)); }

        // 2. 填词
        editor.focus();
        document.execCommand('selectAll', false, null);
        document.execCommand('delete', false, null);
        document.execCommand('insertText', false, task.prompt);
        await new Promise(r => setTimeout(r, 1000));
        
        // 3. 发送
        console.log(">>> 发送指令...");
        editor.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', code: 'Enter', keyCode: 13, which: 13, bubbles: true }));
        document.querySelector('button[class*="send"], button:has(svg)')?.click();

        // 4. 结果监控
        let success = false;
        for (let i = 0; i < 60; i++) {
            // 每秒更新一次锁，防止其他标签页抢活
            localStorage.setItem('jimeng_master_lock', JSON.stringify({ id: TAB_ID, ts: Date.now() }));
            
            await new Promise(r => setTimeout(r, 2000));
            const text = document.body.innerText;
            if (text.includes('再次生成') || text.includes('重新编辑') || text.includes('重新生成')) {
                console.log(">>> [任务完成] 检测到界面更新！");
                success = true;
                break;
            }
        }

        // 5. 下载图片
        if (success) {
            await downloadGeneratedImage(task.id);
        }

        // 6. 结果回传 (CORS 已处理)
        await fetch(`${SERVER_URL}/finish_task?id=${task.id}&status=done&v=${VERSION}`, { 
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        
        lastTaskTime = Date.now(); // 标记任务完成时间
        console.log(">>> [反馈成功]");

    } catch (err) {
        console.error("执行出错:", err);
    }
}

// 启动心跳
setInterval(heartbeat, 3000);
