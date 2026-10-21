// 使用 Node 沙箱模拟页面和本地服务，不启动浏览器或访问网络。
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const source = fs.readFileSync(path.join(__dirname, '../assets/extension/content.js'), 'utf8');

function environment(response) {
    const calls = [];
    const image = {src: 'https://img.jianying.com/new.png', complete: true, naturalWidth: 100};
    const context = vm.createContext({
        console: {log() {}, error() {}, warn() {}, debug() {}},
        Math, Date, JSON, Set, Error, AbortSignal,
        setTimeout: callback => { callback(); return 1; },
        setInterval: () => 1, clearInterval() {},
        localStorage: {getItem: () => null, setItem() {}},
        window: {location: {href: 'https://jimeng.jianying.com/generate'}},
        document: {
            querySelectorAll: selector => selector.startsWith('img') ? [image] : [],
            querySelector: () => null, execCommand() {}, body: {innerText: '再次生成'}
        },
        KeyboardEvent: function () {},
        fetch: async (url, options) => {
            calls.push({url, options});
            return {ok: true, status: 200, json: async () => response};
        }
    });
    vm.runInContext(source + '\nthis.testApi = {downloadGeneratedImage, doTask, heartbeat, generatedImages};', context);
    return {context, calls, image};
}

(async () => {
    let env = environment({success: false, error: '模拟保存失败'});
    await assert.rejects(env.context.testApi.downloadGeneratedImage('test', new Set()), /模拟保存失败/);
    env = environment({success: true});
    await assert.rejects(env.context.testApi.downloadGeneratedImage('test', new Set()), /未确认保存成功/);
    env = environment({success: true, path: 'saved.png'});
    assert.equal(await env.context.testApi.downloadGeneratedImage('test', new Set()), true);
    await assert.rejects(env.context.testApi.downloadGeneratedImage('test', new Set(['https://img.jianying.com/new.png'])), /未找到本轮新增图片/);
    // 页面只有旧图片与残留“再次生成”文案时不得完成任务。
    env = environment({success: true});
    await env.context.testApi.doTask({focus() {}, dispatchEvent() {}}, {id: 'test', prompt: '测试'});
    assert.equal(env.calls.some(call => call.url.includes('status=done')), false);
    assert.equal(env.calls.some(call => call.url.includes('status=failed')), true);
    // 旧图尚未加载也必须计入基线，避免稍后加载时被误认新结果。
    env = environment({success: true});
    env.image.complete = false;
    assert.equal(env.context.testApi.generatedImages().length, 0);
    assert.equal(env.context.testApi.generatedImages(false).length, 1);
    // 领取请求未返回时，下一次心跳不得重复领取。
    env = environment({});
    env.context.document.querySelector = () => ({focus() {}, dispatchEvent() {}});
    let resolveFetch;
    env.context.fetch = url => {
        env.calls.push({url});
        return new Promise(resolve => { resolveFetch = resolve; });
    };
    const firstHeartbeat = env.context.testApi.heartbeat();
    await env.context.testApi.heartbeat();
    assert.equal(env.calls.length, 1);
    resolveFetch({ok: true, status: 200, json: async () => ({})});
    await firstHeartbeat;
    console.log('扩展离线行为测试：7 项通过');
})().catch(error => { console.error(error); process.exitCode = 1; });
