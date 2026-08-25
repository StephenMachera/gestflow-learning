// ==========================================
// GESTFLOW VSCODE BRIDGE — extension.js
// ==========================================
// Connects VSCode to GestFlow desktop app
// via WebSocket on localhost port 8766.
//
// Sends on every change:
//   - Active file path
//   - Cursor line and column
//   - Git branch
//   - Project name
//   - Language
// ==========================================

const vscode = require('vscode')
const WebSocket = require('ws')
const path = require('path')
const { execSync } = require('child_process')

const GESTFLOW_WS_PORT = 8766
const RECONNECT_DELAY  = 3000

let socket         = null
let reconnectTimer = null
let statusBarItem  = null


// ── Activate extension ──
function activate(context) {

    // Create status bar indicator
    statusBarItem = vscode.window.createStatusBarItem(
        vscode.StatusBarAlignment.Right, 100
    )
    statusBarItem.text = '$(plug) GestFlow'
    statusBarItem.tooltip = 'GestFlow connection status'
    statusBarItem.show()
    context.subscriptions.push(statusBarItem)

    // Connect to GestFlow
    connect()

    // Listen for editor changes — send state on every change
    context.subscriptions.push(
        vscode.window.onDidChangeActiveTextEditor(() => {
            sendCurrentState()
        })
    )

    context.subscriptions.push(
        vscode.window.onDidChangeTextEditorSelection(() => {
            sendCurrentState()
        })
    )

    // Listen for GestFlow requesting state
    console.log('GestFlow VSCode Bridge activated')
}


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

        socket.on('open', () => {
            console.log('GestFlow: VSCode connected ✅')
            statusBarItem.text = '$(check) GestFlow'
            statusBarItem.color = '#00ff00'
            clearTimeout(reconnectTimer)

            // Announce connection
            socket.send(JSON.stringify({
                type   : 'VSCODE_CONNECTED',
                version: vscode.version
            }))

            // Send current state immediately
            sendCurrentState()
        })

        socket.on('message', (data) => {
            try {
                const message = JSON.parse(data)
                handleMessage(message)
            } catch(e) {
                console.error('GestFlow: Bad message', e)
            }
        })

        socket.on('close', () => {
            console.log('GestFlow: Disconnected — retrying...')
            statusBarItem.text = '$(plug) GestFlow'
            statusBarItem.color = undefined
            scheduleReconnect()
        })

        socket.on('error', () => {
            scheduleReconnect()
        })

    } catch(e) {
        scheduleReconnect()
    }
}


// ── Handle messages from GestFlow ──
function handleMessage(message) {
    switch(message.type) {

        case 'GET_VSCODE_STATE':
            sendCurrentState(message.requestId)
            break

        case 'OPEN_FILE':
            // Target device asks VSCode to open a file at a line
            if (message.filePath) {
                openFileAtLine(message.filePath, message.cursorLine || 0)
            }
            break

        case 'PING':
            if (socket && socket.readyState === WebSocket.OPEN) {
                socket.send(JSON.stringify({ type: 'PONG' }))
            }
            break

        default:
            console.log('GestFlow: Unknown message', message.type)
    }
}


// ── Get current VSCode state ──
function getCurrentState() {
    const editor = vscode.window.activeTextEditor

    if (!editor) {
        return {
            filePath    : null,
            fileName    : null,
            language    : null,
            cursorLine  : 0,
            cursorColumn: 0,
            projectName : getProjectName(),
            gitBranch   : getGitBranch(),
            isUnsaved   : false
        }
    }

    const document      = editor.document
    const selection     = editor.selection
    const filePath      = document.uri.fsPath
    const absolutePath  = path.resolve(filePath)
    const fileName      = path.basename(absolutePath)
    const cursorLine    = selection.active.line + 1
    const cursorCol     = selection.active.character + 1

    return {
        filePath    : absolutePath,
        fileName    : fileName,
        language    : document.languageId,
        cursorLine  : cursorLine,
        cursorColumn: cursorCol,
        projectName : getProjectName(),
        gitBranch   : getGitBranch(absolutePath),
        isUnsaved   : document.isDirty
    }
}


// ── Send current state to GestFlow ──
function sendCurrentState(requestId = null) {
    if (!socket || socket.readyState !== WebSocket.OPEN) {
        return
    }

    const state = getCurrentState()

    socket.send(JSON.stringify({
        type      : 'VSCODE_STATE_RESPONSE',
        requestId : requestId,
        state     : state
    }))
}


// ── Get git branch ──
function getGitBranch(filePath = null) {
    try {
        // Use file path to find the right repo
        // or fall back to workspace root
        const cwd = filePath
            ? path.dirname(filePath)
            : vscode.workspace.workspaceFolders?.[0]?.uri?.fsPath

        if (!cwd) return null

        const branch = execSync(
            'git branch --show-current',
            { cwd, timeout: 2000, encoding: 'utf8' }
        ).trim()

        return branch || null

    } catch(e) {
        return null  // not a git repo or git not installed
    }
}


// ── Get project name ──
function getProjectName() {
    const folders = vscode.workspace.workspaceFolders
    if (folders && folders.length > 0) {
        return folders[0].name
    }
    return null
}


// ── Open file at specific line (used on receiver device) ──
async function openFileAtLine(filePath, lineNumber) {
    try {
        const uri      = vscode.Uri.file(filePath)
        const document = await vscode.workspace.openTextDocument(uri)
        const editor   = await vscode.window.showTextDocument(document)

        // Move cursor to specific line
        if (lineNumber > 0) {
            const position = new vscode.Position(lineNumber - 1, 0)
            editor.selection = new vscode.Selection(position, position)
            editor.revealRange(
                new vscode.Range(position, position),
                vscode.TextEditorRevealType.InCenter
            )
        }

        console.log(`GestFlow: Opened ${filePath} at line ${lineNumber}`)

    } catch(e) {
        console.error(`GestFlow: Could not open file: ${e.message}`)
    }
}


// ── Reconnect ──
function scheduleReconnect() {
    clearTimeout(reconnectTimer)
    reconnectTimer = setTimeout(connect, RECONNECT_DELAY)
}


// ── Deactivate ──
function deactivate() {
    if (socket) {
        socket.close()
    }
    if (statusBarItem) {
        statusBarItem.dispose()
    }
}

module.exports = { activate, deactivate }