"use client";

import { useState } from "react";
import Editor from "@monaco-editor/react";
import ReactMarkdown from "react-markdown";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { vscDarkPlus } from "react-syntax-highlighter/dist/esm/styles/prism";

interface KernelOptimization {
  iteration: number;
  summary: string;
  time: number;
}

interface AnalysisResult {
  title: string;
  original_code: string;
  best_code: string;
  original_metrics: any;
  best_metrics: any;
  optimization_log: KernelOptimization[];
  final_report: string;
  component_code?: string;
}

interface Message {
  role: "user" | "agent";
  text?: string;
  think?: string;
  viz_data?: AnalysisResult;
  error?: string;
}

export default function Home() {
  const [cudaCode, setCudaCode] = useState<string>("");
  const [chatInput, setChatInput] = useState<string>("");
  const [messages, setMessages] = useState<Message[]>([
    { role: "agent", text: "CUDA 최적화 도우미 Nsight Agent입니다. 코드를 업로드하거나 에디터에 붙여넣기 후 질문을 입력해주세요." }
  ]);
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (e) => {
        const text = e.target?.result as string;
        setCudaCode(text);
      };
      reader.readAsText(file);
    }
  };

  const handleEditorChange = (value: string | undefined) => {
    setCudaCode(value || "");
  };

  const handleSendMessage = async () => {
    if (!chatInput.trim()) return;

    const newMessages: Message[] = [...messages, { role: "user", text: chatInput }];
    setMessages(newMessages);
    setChatInput("");
    setIsAnalyzing(true);

    try {
      const response = await fetch("http://localhost:8000/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ cuda_code: cudaCode, user_question: chatInput }),
      });
      
      if (!response.ok) throw new Error("API Request Failed");

      const data = await response.json();
      
      if (data.error_message) {
        setMessages((prev) => [...prev, { role: "agent", error: data.error_message }]);
      } else {
        setMessages((prev) => [...prev, { role: "agent", viz_data: data.viz_data }]);
      }
    } catch (error) {
      setMessages((prev) => [...prev, { role: "agent", text: "서버와 연결할 수 없거나 분석 중 오류가 발생했습니다." }]);
    } finally {
      setIsAnalyzing(false);
    }
  };

  const CodeRenderer = {
    code({ node, inline, className, children, ...props }: any) {
      const match = /language-(\w+)/.exec(className || "");
      return !inline && match ? (
        <SyntaxHighlighter
          style={vscDarkPlus as any}
          language={match[1]}
          PreTag="div"
          {...props}
        >
          {String(children).replace(/\n$/, "")}
        </SyntaxHighlighter>
      ) : (
        <code className="bg-neutral-900 text-green-400 px-1 py-0.5 rounded text-sm" {...props}>
          {children}
        </code>
      );
    }
  };

  return (
    <div className="flex h-screen bg-neutral-900 text-white font-sans overflow-hidden">
      {/* Left Panel: Code Viewer */}
      <div className="w-1/2 flex flex-col border-r border-neutral-800 bg-neutral-950">
        <div className="p-4 border-b border-neutral-800 flex justify-between items-center bg-neutral-900">
          <h2 className="text-lg font-bold flex items-center gap-2">
            <span className="text-green-500">{"</>"}</span> CUDA Code Editor
          </h2>
          <label className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded cursor-pointer text-sm font-medium transition-colors">
            Upload .cu File
            <input type="file" accept=".cu,.cpp,.c" className="hidden" onChange={handleFileUpload} />
          </label>
        </div>
        <div className="flex-1 overflow-hidden relative">
          <Editor
            height="100%"
            language="cpp"
            theme="vs-dark"
            value={cudaCode}
            onChange={handleEditorChange}
            options={{
              minimap: { enabled: false },
              fontSize: 14,
              wordWrap: "on",
              padding: { top: 16 }
            }}
          />
          {!cudaCode && (
            <div className="absolute inset-0 pointer-events-none flex items-center justify-center text-neutral-500 z-10">
              <span className="bg-neutral-900/80 px-4 py-2 rounded-lg">Upload a CUDA file or paste code here</span>
            </div>
          )}
        </div>
      </div>

      {/* Right Panel: Chat UI */}
      <div className="w-1/2 flex flex-col bg-neutral-900">
        <div className="p-4 border-b border-neutral-800 bg-neutral-900">
          <h2 className="text-lg font-bold flex items-center gap-2">
            <span className="text-blue-500">💬</span> Nsight Agent Chat
          </h2>
        </div>
        
        {/* Messages */}
        <div className="flex-1 overflow-auto p-4 space-y-4">
          {messages.map((msg, i) => (
            <div key={i} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
              <div className={`max-w-[80%] p-4 rounded-lg overflow-hidden ${
                msg.role === "user" 
                  ? "bg-blue-600 text-white" 
                  : "bg-neutral-800 text-neutral-200 border border-neutral-700"
              }`}>
                {msg.role === "agent" ? (
                  <div className="flex flex-col gap-3">
                    {msg.think && (
                      <div className="bg-neutral-900/50 border border-neutral-700/50 p-3 rounded text-neutral-400 text-sm whitespace-pre-wrap">
                        <span className="font-bold text-neutral-500 mb-1 block">💡 Thinking...</span>
                        {msg.think}
                      </div>
                    )}
                    {msg.text && (
                      <div className="prose prose-invert max-w-none break-words">
                        <ReactMarkdown components={CodeRenderer}>
                          {msg.text}
                        </ReactMarkdown>
                      </div>
                    )}
                    {msg.error && (
                      <div className="bg-red-900/20 border border-red-900/50 p-4 rounded-lg text-red-400 text-sm">
                        <strong className="block mb-1">❌ Error Occurred</strong>
                        {msg.error}
                      </div>
                    )}

                    {msg.viz_data && (
                      <div className="flex flex-col gap-6">
                        {/* 1. Final Markdown Report */}
                        <div className="prose prose-invert max-w-none break-words bg-neutral-900 p-6 rounded-xl border border-neutral-700 shadow-xl">
                          <ReactMarkdown components={CodeRenderer}>
                            {msg.viz_data.final_report}
                          </ReactMarkdown>
                        </div>

                        {/* 1.5. Dynamic Visualization Component (if exists) */}
                        {msg.viz_data.component_code && (
                          <div className="bg-neutral-900 p-6 rounded-xl border border-blue-900/30 shadow-inner">
                            <h4 className="text-xs font-bold text-blue-400 uppercase mb-4 flex items-center gap-2">
                              <span className="animate-pulse">📊</span> AI Generated Insights
                            </h4>
                            <div className="prose prose-invert max-w-none">
                              {/* Since we can't safely eval JSX string without heavy libs, 
                                  we display it as an advanced code insight for now */}
                              <ReactMarkdown components={CodeRenderer}>
                                {`\`\`\`jsx\n${msg.viz_data.component_code}\n\`\`\``}
                              </ReactMarkdown>
                            </div>
                          </div>
                        )}
                        
                        {/* 2. Optimization Log Table */}
                        <div className="bg-neutral-950 p-4 rounded-lg border border-neutral-800">
                          <h4 className="text-sm font-bold text-neutral-400 uppercase tracking-wider mb-3">Optimization History</h4>
                          <div className="overflow-hidden rounded-md border border-neutral-800">
                            <table className="w-full text-left text-sm border-collapse">
                              <thead>
                                <tr className="bg-neutral-900 text-neutral-300">
                                  <th className="p-2 border-b border-neutral-800">Iter</th>
                                  <th className="p-2 border-b border-neutral-800">Summary</th>
                                  <th className="p-2 border-b border-neutral-800 text-right">Time (ms)</th>
                                </tr>
                              </thead>
                              <tbody>
                                {msg.viz_data.optimization_log.map((log, idx) => (
                                  <tr key={idx} className="border-b border-neutral-900 hover:bg-neutral-900/50 transition-colors">
                                    <td className="p-2 text-neutral-500 font-mono">{log.iteration}</td>
                                    <td className="p-2 text-neutral-200">{log.summary}</td>
                                    <td className="p-2 text-right text-green-400 font-mono">{log.time.toFixed(3)}</td>
                                  </tr>
                                ))}
                              </tbody>
                            </table>
                          </div>
                        </div>

                        {/* 3. Metrics Comparison */}
                        <div className="grid grid-cols-2 gap-4">
                          <div className="bg-neutral-900 p-4 rounded-lg border border-neutral-800">
                            <span className="text-xs font-bold text-neutral-500 uppercase block mb-1">Baseline</span>
                            <div className="text-2xl font-mono text-neutral-300">
                              {msg.viz_data.original_metrics.execution_time_ms.toFixed(3)}<span className="text-sm ml-1 text-neutral-500">ms</span>
                            </div>
                          </div>
                          <div className="bg-neutral-900 p-4 rounded-lg border border-neutral-800">
                            <span className="text-xs font-bold text-green-500 uppercase block mb-1">Best Optimized</span>
                            <div className="text-2xl font-mono text-green-400">
                              {msg.viz_data.best_metrics.execution_time_ms.toFixed(3)}<span className="text-sm ml-1 text-neutral-500">ms</span>
                            </div>
                          </div>
                        </div>

                        {/* 4. Best Code Snippet */}
                        <div className="bg-neutral-950 rounded-lg border border-neutral-800 overflow-hidden">
                          <div className="bg-neutral-900 px-4 py-2 border-b border-neutral-800 flex justify-between items-center">
                            <span className="text-xs font-bold text-neutral-400 uppercase">Best Performing Kernel</span>
                            <button 
                              onClick={() => setCudaCode(msg.viz_data!.best_code)}
                              className="text-xs bg-blue-600 hover:bg-blue-700 text-white px-2 py-1 rounded transition-colors"
                            >
                              Load into Editor
                            </button>
                          </div>
                          <SyntaxHighlighter
                            style={vscDarkPlus as any}
                            language="cpp"
                            PreTag="div"
                            customStyle={{ margin: 0, padding: "1rem", fontSize: "0.8rem" }}
                          >
                            {msg.viz_data.best_code}
                          </SyntaxHighlighter>
                        </div>
                      </div>
                    )}
                  </div>
                ) : (
                  msg.text
                )}
              </div>
            </div>
          ))}
          {isAnalyzing && (
            <div className="flex justify-start">
              <div className="bg-neutral-800 text-neutral-300 p-4 rounded-lg border border-neutral-700 flex items-center gap-3">
                <div className="animate-spin h-5 w-5 border-2 border-green-500 border-t-transparent rounded-full"></div>
                <span className="animate-pulse">💡 Nsight Agent is thinking...</span>
              </div>
            </div>
          )}
        </div>

        {/* Input area */}
        <div className="p-4 border-t border-neutral-800 bg-neutral-950">
          <div className="flex gap-2">
            <input
              type="text"
              value={chatInput}
              onChange={(e) => setChatInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSendMessage()}
              placeholder="Ask about optimizations, bottlenecks, or profiling..."
              className="flex-1 bg-neutral-800 border border-neutral-700 rounded-lg px-4 py-3 focus:outline-none focus:border-green-500 transition-colors"
            />
            <button 
              onClick={handleSendMessage}
              disabled={isAnalyzing}
              className="bg-green-600 hover:bg-green-700 disabled:bg-neutral-700 text-white px-6 py-3 rounded-lg font-medium transition-colors"
            >
              Send
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
