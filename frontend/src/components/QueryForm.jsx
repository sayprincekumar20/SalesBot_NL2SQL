// src/components/QueryForm.jsx
import React, { useState } from "react";
import {
  BarChart, Bar, LineChart, Line,
  PieChart, Pie, Cell,
  XAxis, YAxis, Tooltip, Legend, CartesianGrid, ResponsiveContainer
} from "recharts";
import { motion } from "framer-motion";
import { User, Bot } from "lucide-react"; // avatar icons

const COLORS = ["#3b82f6", "#10b981", "#f59e0b", "#f87171", "#a78bfa", "#ec4899", "#14b8a6"];

// Chat bubble with avatar
const ChatBubble = ({ role = "bot", children }) => (
  <motion.div
    initial={{ opacity: 0, y: 10 }}
    animate={{ opacity: 1, y: 0 }}
    transition={{ duration: 0.3 }}
    className={`flex items-start gap-3 max-w-4xl ${
      role === "user" ? "ml-auto flex-row-reverse" : "mr-auto"
    }`}
  >
    {/* Avatar */}
    <div
      className={`p-3 rounded-full shadow-md ${
        role === "user" ? "bg-blue-600 text-white" : "bg-gray-200 text-gray-700"
      }`}
    >
      {role === "user" ? <User size={22} /> : <Bot size={22} />}
    </div>

    {/* Bubble */}
    <div
      className={`px-5 py-4 rounded-2xl shadow-md max-w-xl ${
        role === "user"
          ? "bg-blue-600 text-white"
          : "bg-white text-gray-800"
      }`}
    >
      {children}
    </div>
  </motion.div>
);

// Simple card
const Card = ({ children }) => (
  <div className="p-4 w-full bg-white rounded-xl shadow-sm border border-gray-200">
    {children}
  </div>
);

// Data table
const DataTable = ({ data, title }) => {
  if (!data?.length) return null;
  const columns = Object.keys(data[0]);
  return (
    <Card>
      {title && <h2 className="text-xl font-bold mb-3">{title}</h2>}
      <div className="overflow-x-auto">
        <table className="w-full border-collapse text-base">
          <thead>
            <tr className="bg-blue-50">
              {columns.map((col) => (
                <th key={col} className="px-4 py-2 border text-left">{col}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {data.map((row, idx) => (
              <tr key={idx} className="hover:bg-gray-50">
                {columns.map((col) => (
                  <td key={col} className="px-4 py-2 border">{row[col]}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Card>
  );
};

const QueryForm = () => {
  const [prompt, setPrompt] = useState("");
  const [messages, setMessages] = useState([]); // chat history
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!prompt.trim()) return;

    // push user prompt
    setMessages((prev) => [...prev, { role: "user", content: prompt }]);

    setLoading(true);
    try {
      const res = await fetch("http://127.0.0.1:8000/query", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt }),
      });
      const data = await res.json();

      // push bot response
      setMessages((prev) => [...prev, { role: "bot", content: data }]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        { role: "bot", content: { message: `❌ Error: ${err.message}` } },
      ]);
    } finally {
      setPrompt("");
      setLoading(false);
    }
  };

  const mergeForecastData = (labels, datasets, forecast) => {
    if (!forecast?.points) {
      return labels.map((l, i) => {
        const obj = { name: l };
        datasets.forEach((ds) => (obj[ds.name] = ds.data[i]));
        return obj;
      });
    }

    const forecastMap = new Map(forecast.points.map((p) => [p.period, p.value]));
    const mergedLabels = Array.from(
      new Set([...labels, ...forecast.points.map((p) => p.period)])
    );

    return mergedLabels.map((label) => {
      const obj = { name: label };
      datasets.forEach((ds) => {
        obj[ds.name] = ds.data[labels.indexOf(label)] ?? null;
      });
      if (forecastMap.has(label)) obj.Forecast = forecastMap.get(label);
      return obj;
    });
  };

  const renderChart = (resp) => {
    if (!resp?.chart) return null;
    const { type, labels, datasets } = resp.chart;
    if (type === "table") return <DataTable data={resp.data} />;
    if (!labels || !datasets) return null;

    const chartData = mergeForecastData(labels, datasets, resp.forecast);

    switch (type) {
      case "bar":
        return (
          <ResponsiveContainer width="100%" height={400}>
            <BarChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip />
              <Legend />
              {datasets.map((ds) => (
                <Bar key={ds.name} dataKey={ds.name}>
                  {chartData.map((entry, idx) => (
                    <Cell key={`cell-${idx}`} fill={COLORS[idx % COLORS.length]} />
                  ))}
                </Bar>
              ))}
              {resp.forecast && (
                <Bar dataKey="Forecast">
                  {chartData.map((_, idx) => (
                    <Cell key={idx} fill="#2563eb" />
                  ))}
                </Bar>
              )}
            </BarChart>
          </ResponsiveContainer>
        );
      case "line":
        return (
          <ResponsiveContainer width="100%" height={400}>
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip />
              <Legend />
              {datasets.map((ds, idx) => (
                <Line
                  key={ds.name}
                  dataKey={ds.name}
                  stroke={COLORS[idx % COLORS.length]}
                  strokeWidth={2}
                />
              ))}
              {resp.forecast && (
                <Line
                  dataKey="Forecast"
                  stroke="#2563eb"
                  strokeWidth={3}
                  strokeDasharray="5 5"
                />
              )}
            </LineChart>
          </ResponsiveContainer>
        );
      case "pie":
        return (
          <ResponsiveContainer width="100%" height={400}>
            <PieChart>
              <Tooltip />
              <Legend />
              <Pie
                data={chartData}
                dataKey={datasets[0].name}
                nameKey="name"
                outerRadius={150}
                label
              >
                {chartData.map((entry, idx) => (
                  <Cell key={idx} fill={COLORS[idx % COLORS.length]} />
                ))}
              </Pie>
            </PieChart>
          </ResponsiveContainer>
        );
      default:
        return null;
    }
  };

  return (
    <div className="min-h-screen flex flex-col bg-gray-100">
      {/* Chat area */}
      <div className="flex-1 p-6 overflow-y-auto space-y-6">
        {messages.map((msg, idx) => (
          <ChatBubble key={idx} role={msg.role}>
            {msg.role === "user" ? (
              <p className="text-lg">{msg.content}</p>
            ) : (
              <div className="space-y-4">
                {msg.content.intent && (
                  <p><strong>Intent:</strong> {msg.content.intent}</p>
                )}
                {msg.content.message && (
                  <p><strong>Message:</strong> {msg.content.message}</p>
                )}
                {msg.content.query && (
                  <Card>
                    <h2 className="font-bold">Executed SQL:</h2>
                    <pre className="bg-gray-100 p-3 rounded text-sm overflow-x-auto">
                      {msg.content.query}
                    </pre>
                  </Card>
                )}
                {msg.content.summary && (
                  <Card>
                    <h2 className="font-bold mb-2">Summary:</h2>
                    <p className="whitespace-pre-line">{msg.content.summary}</p>
                  </Card>
                )}
                {msg.content.data && <DataTable data={msg.content.data} title="Data Table" />}
                {renderChart(msg.content)}
                {msg.content.intent === "forecast" && (
                  <DataTable data={msg.content.forecast?.points} title="Forecast Data" />
                )}
              </div>
            )}
          </ChatBubble>
        ))}
        {loading && <p className="text-gray-500 italic">⏳ Running query...</p>}
      </div>

      {/* Input bar */}
      <form
        onSubmit={handleSubmit}
        className="sticky bottom-0 w-full bg-white p-4 shadow-md flex gap-3"
      >
        <input
          type="text"
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          placeholder="Ask something like 'Sales by ShipRegion' – view results in different chart types!"
          className="flex-1 border rounded-lg px-4 py-3 text-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        <button
          type="submit"
          disabled={loading}
          className="bg-blue-600 text-white px-6 py-3 rounded-lg font-medium hover:bg-blue-700 disabled:opacity-50"
        >
          {loading ? "Running..." : "Send"}
        </button>
      </form>
    </div>
  );
};
export default QueryForm;
