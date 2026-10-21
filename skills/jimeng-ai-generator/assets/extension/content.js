// 即梦本地任务助手；只有新增图片确实保存后才报告完成。
const VERSION = "1.17";
const SERVER_URL = 'http://localhost:18542';
const TAB_ID = Math.random().toString(36).substring(7);
let isProcessingTask = false;
let lastTaskTime = 0;
const wait = ms => new Promise(resolve => setTimeout(resolve, ms));

function refreshLock() {
    localStorage.setItem('jimeng_master_lock', JSON.stringify({id: TAB_ID, ts: Date.now()}));
}

function tryGetMasterLock() {
    let lock = {};
    try { lock = JSON.parse(localStorage.getItem('jimeng_master_lock') || '{}'); }
    catch (error) { console.warn('任务锁格式无效，将重新获取'); }
    if (!lock.id || Date.now() - lock.ts > 10000 || lock.id === TAB_ID) {
        refreshLock();
        return true;
    }
    return false;
}

async function requestJson(path, options = {}) {
    const response = await fetch(`${SERVER_URL}${path}`, {
        ...options, signal: AbortSignal.timeout(45000)
    });
    const data = await response.json();
    if (!response.ok || data.success === false) {
        throw new Error(data.error || `本地接口失败：HTTP ${response.status}`);
    }
    return data;
}

function generatedImages(loadedOnly = true) {
    return Array.from(document.querySelectorAll('img[src*="jianying"], img[src*="seaway"]'))
        .filter(img => !loadedOnly || (img.complete && img.naturalWidth > 0))
        .map(img => img.src);
}

async function downloadGeneratedImage(taskId, previousUrls) {
    const imageUrl = generatedImages().find(url => !previousUrls.has(url));
    if (!imageUrl) throw new Error('未找到本轮新增图片');
    const result = await requestJson('/save_image', {
        method: 'POST', headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({taskId, url: imageUrl})
    });
    if (result.success !== true || !result.path) throw new Error('服务器未确认保存成功');
    return true;
}

async function heartbeat() {
    if (isProcessingTask || Date.now() - lastTaskTime < 10000 || !tryGetMasterLock()) return;
    const editor = document.querySelector('[contenteditable="true"]');
    if (!editor || !window.location.href.includes('generate')) return;
    isProcessingTask = true;
    try {
        const task = await requestJson(`/get_task?v=${VERSION}`);
        if (task.id) {
            await doTask(editor, task);
        }
    } catch (error) {
        // 本地服务未启动时保持页面可用，不声称任务成功。
        console.debug('即梦本地服务暂不可用');
    } finally {
        isProcessingTask = false;
    }
}

async function doTask(editor, task) {
    const lockTimer = setInterval(refreshLock, 3000);
    try {
        const v4Button = Array.from(document.querySelectorAll('button, span, div'))
            .find(el => (el.innerText || el.textContent || '').includes('4.0'));
        if (v4Button) { v4Button.click(); await wait(1000); }
        // 在真正提交前记录已有图片，避免完成按钮残留导致旧图被认作新结果。
        const previousUrls = new Set(generatedImages(false));
        editor.focus();
        document.execCommand('selectAll', false, null);
        document.execCommand('delete', false, null);
        document.execCommand('insertText', false, task.prompt);
        await wait(1000);
        editor.dispatchEvent(new KeyboardEvent('keydown', {
            key: 'Enter', code: 'Enter', keyCode: 13, which: 13, bubbles: true
        }));
        document.querySelector('button[class*="send"], button:has(svg)')?.click();
        let hasNewImage = false;
        for (let attempt = 0; attempt < 60; attempt++) {
            await wait(2000);
            if (generatedImages().some(url => !previousUrls.has(url))) {
                hasNewImage = true;
                break;
            }
        }
        if (!hasNewImage) throw new Error('等待新增图片超时');
        await downloadGeneratedImage(task.id, previousUrls);
        await requestJson(`/finish_task?id=${encodeURIComponent(task.id)}&status=done&v=${VERSION}`, {
            method: 'POST', headers: {'Content-Type': 'application/json'}
        });
        console.log('任务图片已保存并确认完成');
    } catch (error) {
        console.error('任务失败，未标记完成：', error.message);
        try {
            await requestJson(`/finish_task?id=${encodeURIComponent(task.id)}&status=failed&v=${VERSION}`, {
                method: 'POST', headers: {'Content-Type': 'application/json'}
            });
        } catch (reportError) {
            console.error('失败状态未送达；请检查本地服务，不要自动重复生成');
        }
    } finally {
        clearInterval(lockTimer);
        lastTaskTime = Date.now();
    }
}

setInterval(heartbeat, 3000);
