// ==========================================
// GESTFLOW BROWSER BRIDGE — background.js
// Manifest V3 with alarms-based keep-alive
// ==========================================

const GESTFLOW_WS_PORT = 8765
const RECONNECT_DELAY  = 3000

let socket = null
let reconnectTimer = null


// ── Keep alive using Chrome Alarms API ──
// This is the CORRECT way to keep V3 service workers alive
// Alarms fire every minute and wake the service worker up
chrome.alarms.create('gestflow-keepalive', {
  periodInMinutes: 0.4   // fires every 24 seconds
})

chrome.alarms.onAlarm.addListener((alarm) => {
  if (alarm.name === 'gestflow-keepalive') {
    // Wake up — check connection status
    if (!socket || socket.readyState !== WebSocket.OPEN) {
      console.log('GestFlow: Alarm fired — reconnecting...')
      connect()
    } else {
      // Already connected — send ping to confirm
      socket.send(JSON.stringify({ type: 'PING' }))
      console.log('GestFlow: Alarm fired — still connected ✅')
    }
  }
})

chrome.tabs.onActivated.addListener((activeInfo) => {
  if (socket && socket.readyState === WebSocket.OPEN) {
    chrome.tabs.get(activeInfo.tabId, (tab) => {
      if (tab && tab.url &&
          !tab.url.startsWith('chrome://') &&
          !tab.url.startsWith('chrome-extension://')) {
        socket.send(JSON.stringify({
          type : 'TAB_SWITCHED',
          url  : tab.url,
          title: tab.title,
          tabId: tab.id
        }))
      }
    })
  }
})
// ── Connect to GestFlow ──
function connect() {
  if (socket) {
    socket.onclose = null
    socket.onerror = null
    try { socket.close() } catch(e) {}
    socket = null
  }

  try {
    socket = new WebSocket(`ws://localhost:${GESTFLOW_WS_PORT}`)

    socket.onopen = () => {
      console.log('GestFlow: Connected ✅')
      clearTimeout(reconnectTimer)

      socket.send(JSON.stringify({
        type   : 'BROWSER_CONNECTED',
        browser: getBrowserName()
      }))
    }

    socket.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data)
        handleMessage(message)
      } catch(e) {
        console.error('GestFlow: Bad message', e)
      }
    }

    socket.onclose = () => {
      console.log('GestFlow: Disconnected — retrying in 3s')
      scheduleReconnect()
    }

    socket.onerror = () => {
      socket.close()
    }

  } catch(e) {
    scheduleReconnect()
  }
}


// ── Handle messages from GestFlow ──
function handleMessage(message) {
  switch(message.type) {

    case 'GET_ACTIVE_TAB':
      chrome.tabs.query(
        { active: true, currentWindow: true },
        (tabs) => {
          const tab = tabs.find(t =>
            t.url &&
            !t.url.startsWith('chrome://') &&
            !t.url.startsWith('chrome-extension://') &&
            !t.url.startsWith('about:')
          )

          if (socket && socket.readyState === WebSocket.OPEN) {
            socket.send(JSON.stringify({
              type      : 'ACTIVE_TAB_RESPONSE',
              requestId : message.requestId,   // ← echo back
              url       : tab ? tab.url   : null,
              title     : tab ? tab.title : null,
            }))
          }
        }
      )
      break

    case 'GET_ALL_TABS':
      chrome.tabs.query({}, (tabs) => {
        if (socket && socket.readyState === WebSocket.OPEN) {
          socket.send(JSON.stringify({
            type: 'ALL_TABS_RESPONSE',
            tabs: tabs.map(t => ({
              url  : t.url,
              title: t.title,
              tabId: t.id,
            }))
          }))
        }
      })
      break

    case 'OPEN_URL':
      if (message.url) {
        chrome.tabs.create({ url: message.url })
      }
      break

    case 'PONG':
      console.log('GestFlow: Pong received ✅')
      break

    default:
      console.log('GestFlow: Unknown message', message.type)
  }
}


// ── Helpers ──
function getBrowserName() {
  const ua = navigator.userAgent.toLowerCase()
  if (ua.includes('brave'))  return 'brave'
  if (ua.includes('edg'))    return 'edge'
  if (ua.includes('chrome')) return 'chrome'
  return 'chromium'
}

function scheduleReconnect() {
  clearTimeout(reconnectTimer)
  reconnectTimer = setTimeout(connect, RECONNECT_DELAY)
}


// ── Start ──
connect()