const fs = require('node:fs');

const scenario = process.env.XP005_SCENARIO || 'step_one';
const trace = process.env.XP005_TRACE;
const target = {
  id: 'local-verification-tab', type: 'page',
  url: 'https://www.youtube.com/verify', webSocketDebuggerUrl: 'ws://local.invalid/fixture',
};

function record(event) {
  if (trace) fs.appendFileSync(trace, event + '\n');
}

function client() {
  return {
    close: async () => {},
    Runtime: {
      evaluate: async ({ expression, returnByValue }) => {
        if (expression.includes('window.name===')) return { result: { value: true } };
        if (expression.includes('document.body?.innerText')) {
          const body = scenario === 'step_two'
            ? 'Phone verification (step 2 of 2) Enter the SMS code'
            : 'Phone verification (step 1 of 2) Send verification code';
          return { result: { value: body } };
        }
        if (expression.includes('querySelectorAll')) {
          if (scenario === 'before_click' && expression.includes('button,')) {
            return { result: {} };
          }
          return { result: { objectId: expression.includes('button,') ? 'next' : 'phone' } };
        }
        return { result: { value: returnByValue ? true : null } };
      },
      callFunctionOn: async ({ returnByValue }) => ({
        result: { value: returnByValue ? { ok: true, x: 20, y: 20 } : undefined },
      }),
    },
    Input: {
      dispatchKeyEvent: async () => {},
      insertText: async () => {},
      dispatchMouseEvent: async ({ type }) => {
        if (type === 'mousePressed') {
          record('mousePressed');
          if (scenario === 'during_click') throw Error('fixture transport lost');
        }
      },
    },
  };
}

async function CDP() { return client(); }
CDP.List = async () => [target];
module.exports = CDP;
