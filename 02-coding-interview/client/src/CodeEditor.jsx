import React, { useEffect, useState, useRef } from 'react';
import Editor from '@monaco-editor/react';
import { io } from 'socket.io-client';

const CodeEditor = () => {
    const [code, setCode] = useState('// Start coding here...');
    const [language, setLanguage] = useState('javascript');
    const [output, setOutput] = useState('');
    const [isRunning, setIsRunning] = useState(false);
    const socketRef = useRef(null);
    const editorRef = useRef(null);

    // Use a fixed session ID for now, or generate one from URL
    const sessionId = 'default-session';

    useEffect(() => {
        // Connect to backend
        socketRef.current = io();

        socketRef.current.emit('join-session', sessionId);

        socketRef.current.on('init-session', (data) => {
            setCode(data.code);
            setLanguage(data.language);
        });

        socketRef.current.on('code-update', (newCode) => {
            if (editorRef.current) {
                const model = editorRef.current.getModel();
                if (model && model.getValue() !== newCode) {
                    // Only update if content is different to avoid cursor jumping
                    // Ideally we would use operational transforms or CRDTs, but for this homework simple replacement is okay
                    // if we are careful. However, setValue will reset cursor.
                    // A better approach for simple sync is just updating the state and letting the editor update,
                    // but we need to be careful about loops.
                    // For this simple implementation, we'll just update the state.
                    setCode(newCode);
                }
            }
        });

        socketRef.current.on('language-update', (newLanguage) => {
            setLanguage(newLanguage);
        });

        return () => {
            socketRef.current.disconnect();
        };
    }, []);

    const handleEditorChange = (value) => {
        setCode(value);
        socketRef.current.emit('code-change', { sessionId, code: value });
    };

    const handleLanguageChange = (e) => {
        const newLanguage = e.target.value;
        setLanguage(newLanguage);
        socketRef.current.emit('language-change', { sessionId, language: newLanguage });
    };

    const handleEditorDidMount = (editor, monaco) => {
        editorRef.current = editor;
    };

    const runCode = async () => {
        setIsRunning(true);
        setOutput('Running...');

        try {
            if (language === 'javascript') {
                // Safe-ish execution using Function (still has access to global scope, but better than eval)
                // For better security we would use a Web Worker or iframe sandbox.
                // Capturing console.log
                const logs = [];
                const originalLog = console.log;
                console.log = (...args) => logs.push(args.join(' '));

                try {
                    // eslint-disable-next-line no-new-func
                    new Function(code)();
                } catch (e) {
                    logs.push('Error: ' + e.message);
                }

                console.log = originalLog;
                setOutput(logs.join('\n'));

            } else if (language === 'python') {
                // Load Pyodide if not loaded
                if (!window.pyodide) {
                    setOutput('Loading Python runtime...');
                    // We need to load pyodide script in index.html or dynamically here.
                    // For now assuming it's loaded or we load it.
                    // Let's assume we added the script tag in index.html as per plan/task.
                    // Or we can dynamically load it.
                    if (!window.loadPyodide) {
                        setOutput('Pyodide not loaded. Please refresh or check connection.');
                        setIsRunning(false);
                        return;
                    }
                    window.pyodide = await window.loadPyodide();
                }

                // Redirect stdout
                window.pyodide.setStdout({ batched: (msg) => setOutput((prev) => prev + msg + '\n') });
                // Clear previous output if needed, or just append. 
                // For this simple app, maybe just show result.
                // Actually setStdout is for print().

                // Reset output for new run
                setOutput('');

                try {
                    await window.pyodide.runPythonAsync(code);
                } catch (err) {
                    setOutput((prev) => prev + 'Error: ' + err.message);
                }
            } else {
                setOutput('Execution not supported for this language.');
            }
        } catch (error) {
            setOutput('Error: ' + error.message);
        } finally {
            setIsRunning(false);
        }
    };

    return (
        <div className="flex flex-col h-screen bg-gray-900 text-white">
            <header className="flex items-center justify-between p-4 bg-gray-800 border-b border-gray-700">
                <h1 className="text-xl font-bold">Collaborative Code Editor</h1>
                <div className="flex items-center gap-4">
                    <select
                        value={language}
                        onChange={handleLanguageChange}
                        className="bg-gray-700 text-white px-3 py-1 rounded border border-gray-600 focus:outline-none focus:border-blue-500"
                    >
                        <option value="javascript">JavaScript</option>
                        <option value="python">Python</option>
                    </select>
                    <button
                        onClick={runCode}
                        disabled={isRunning}
                        className={`px-4 py-1 rounded font-medium ${isRunning
                            ? 'bg-gray-600 cursor-not-allowed'
                            : 'bg-green-600 hover:bg-green-700'
                            }`}
                    >
                        {isRunning ? 'Running...' : 'Run'}
                    </button>
                </div>
            </header>

            <div className="flex flex-1 overflow-hidden">
                <div className="flex-1 border-r border-gray-700">
                    <Editor
                        height="100%"
                        theme="vs-dark"
                        language={language}
                        value={code}
                        onChange={handleEditorChange}
                        onMount={handleEditorDidMount}
                        options={{
                            minimap: { enabled: false },
                            fontSize: 14,
                            automaticLayout: true,
                        }}
                    />
                </div>
                <div className="w-1/3 bg-gray-900 flex flex-col">
                    <div className="p-2 bg-gray-800 border-b border-gray-700 font-semibold">
                        Output
                    </div>
                    <pre className="flex-1 p-4 font-mono text-sm overflow-auto whitespace-pre-wrap text-gray-300">
                        {output}
                    </pre>
                </div>
            </div>
        </div>
    );
};

export default CodeEditor;
