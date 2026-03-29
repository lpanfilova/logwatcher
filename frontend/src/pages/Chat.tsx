import {
  useEffect,
  useRef,
  useState,
  type FormEvent,
  type KeyboardEvent,
} from "react";
import { Button, Container, Form, Spinner } from "react-bootstrap";
import { MdSend, MdPerson, MdSmartToy } from "react-icons/md";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { apiClient } from "../api";

const DEFAULT_MAX_LOGS = 200;
type ChatMessage = {
  id: string;
  role: "user" | "assistant";
  content: string;
  status: "loading" | "error" | "done";
  matchedCount?: number;
};

const normalizeAssistantContent = (content: string): string => {
  return content
    .replace(/\r\n/g, "\n")
    .replace(/[ \t]+\n/g, "\n")
    .replace(/\n{3,}/g, "\n\n")
    .trim();
};

const Chat = () => {
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const transcriptRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    const transcript = transcriptRef.current;
    if (!transcript) {
      return;
    }

    transcript.scrollTop = transcript.scrollHeight;
  }, [messages]);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    const trimmedQuestion = question.trim();
    if (!trimmedQuestion) {
      return;
    }

    const userMessageId = `user-${Date.now()}`;
    const assistantMessageId = `assistant-${Date.now()}`;

    setMessages((currentMessages) => [
      ...currentMessages,
      {
        id: userMessageId,
        role: "user",
        content: trimmedQuestion,
        status: "done",
      },
      {
        id: assistantMessageId,
        role: "assistant",
        content: "Thinking...",
        status: "loading",
      },
    ]);

    setQuestion("");

    try {
      setLoading(true);
      const chatResponse = await apiClient.askChat(
        trimmedQuestion,
        DEFAULT_MAX_LOGS,
      );

      setMessages((currentMessages) =>
        currentMessages.map((message) =>
          message.id === assistantMessageId
            ? {
                ...message,
                content: normalizeAssistantContent(chatResponse.answer),
                matchedCount: chatResponse.matched_count,
                status: "done",
              }
            : message,
        ),
      );
    } catch (err) {
      console.error("Failed to fetch AI response:", err);
      setMessages((currentMessages) =>
        currentMessages.map((message) =>
          message.id === assistantMessageId
            ? {
                ...message,
                content: "Failed to contact the AI service.",
                status: "error",
              }
            : message,
        ),
      );
    } finally {
      setLoading(false);
    }
  };

  const handleQuestionKeyDown = (event: KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key !== "Enter" || event.shiftKey) {
      return;
    }

    event.preventDefault();

    if (!loading && question.trim()) {
      void handleSubmit(event as unknown as FormEvent<HTMLFormElement>);
    }
  };

  const renderAssistantMessage = (message: ChatMessage) => {
    if (message.status === "loading") {
      return (
        <div className="d-flex align-items-center gap-2 text-muted">
          <Spinner size="sm" />
          <span>{message.content}</span>
        </div>
      );
    }

    return (
      <>
        <div style={{ wordBreak: "break-word" }}>
          <ReactMarkdown
            remarkPlugins={[remarkGfm]}
            components={{
              p: ({ node, ...props }) => <p className="mb-3" {...props} />,
              ul: ({ node, ...props }) => (
                <ul className="mb-3 ps-4" {...props} />
              ),
              ol: ({ node, ...props }) => (
                <ol className="mb-3 ps-4" {...props} />
              ),
              code: ({ node, className, children, ...props }) => (
                <code
                  className={className}
                  style={{
                    backgroundColor: "#f8f9fa",
                    borderRadius: "4px",
                    padding: "0.15rem 0.35rem",
                  }}
                  {...props}
                >
                  {children}
                </code>
              ),
              pre: ({ node, ...props }) => (
                <pre
                  className="mb-3 p-3 border rounded bg-light"
                  style={{ whiteSpace: "pre-wrap" }}
                  {...props}
                />
              ),
            }}
          >
            {message.content}
          </ReactMarkdown>
        </div>
        {typeof message.matchedCount === "number" && (
          <small className="text-muted d-block mt-2">
            Matched logs: {message.matchedCount}
          </small>
        )}
      </>
    );
  };

  return (
    <Container
      fluid
      className="p-4 d-flex flex-column"
      style={{ height: "calc(100vh - 40px)" }}
    >
      {/* Header */}
      <div
        className="shadow-lg border-0 mb-4 position-relative overflow-hidden"
        style={{
          borderRadius: "15px",
          background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
          color: "white",
        }}
      >
        <div className="p-4">
          <div className="d-flex align-items-center justify-content-center mb-2">
            <i className="bi bi-robot me-3" style={{ fontSize: "2rem" }}></i>
            <h2 className="fw-bold mb-0">AI Assistant</h2>
          </div>
          <div className="text-center opacity-75">
            <small className="d-block">
              <i className="bi bi-chat-dots me-1"></i>
              Ask questions about your logs and get intelligent insights
            </small>
          </div>
        </div>
      </div>

      {/* Chat Interface */}
      <div
        className="shadow-lg border-0 grow d-flex flex-column overflow-hidden position-relative"
        style={{
          borderRadius: "15px",
          background: "white",
          backdropFilter: "blur(10px)",
        }}
      >
        {/* Messages Area */}
        <div
          ref={transcriptRef}
          className="grow overflow-auto p-4"
          style={{
            background: "linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%)",
            minHeight: "400px",
          }}
        >
          {messages.length === 0 ? (
            <div className="d-flex align-items-center justify-content-center h-100">
              <div className="text-center text-muted">
                <i
                  className="bi bi-chat-square-dots"
                  style={{ fontSize: "4rem", color: "#6c757d" }}
                ></i>
                <h5 className="mt-3 mb-2">Start a Conversation</h5>
                <p className="mb-0">Ask me anything about your recent logs!</p>
                <small className="text-muted mt-2 d-block">
                  Example: "Summarize errors in the last 10 minutes"
                </small>
              </div>
            </div>
          ) : (
            <div className="d-flex flex-column gap-4">
              {messages.map((message) => (
                <div
                  key={message.id}
                  className={`d-flex ${
                    message.role === "user"
                      ? "justify-content-end"
                      : "justify-content-start"
                  }`}
                >
                  <div
                    className={`position-relative ${
                      message.role === "user"
                        ? "bg-primary text-white"
                        : message.status === "error"
                          ? "bg-danger-subtle border border-danger text-danger"
                          : "bg-white shadow-sm"
                    }`}
                    style={{
                      maxWidth: "75%",
                      borderRadius:
                        message.role === "user"
                          ? "18px 18px 4px 18px"
                          : "18px 18px 18px 4px",
                      padding: "16px 20px",
                      wordBreak: "break-word",
                    }}
                  >
                    {/* Avatar/Icon */}
                    <div
                      className="position-absolute d-flex align-items-center justify-content-center"
                      style={{
                        width: "32px",
                        height: "32px",
                        borderRadius: "50%",
                        background:
                          message.role === "user"
                            ? "linear-gradient(135deg, #007eea 0%, #764ba2 100%)"
                            : "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
                        top: "-8px",
                        [message.role === "user" ? "right" : "left"]: "-8px",
                        border: "2px solid white",
                      }}
                    >
                      {message.role === "user" ? (
                        <MdPerson size={14} color="white" />
                      ) : (
                        <MdSmartToy size={14} color="white" />
                      )}
                    </div>

                    <div style={{ marginTop: "8px" }}>
                      {message.role === "user" ? (
                        <div className="fw-medium">{message.content}</div>
                      ) : (
                        renderAssistantMessage(message)
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Input Area */}
        <div
          className="border-top border-light p-4"
          style={{
            background: "white",
            borderRadius: "0 0 15px 15px",
          }}
        >
          <Form onSubmit={handleSubmit}>
            <Form.Group controlId="chatQuestion">
              <div className="position-relative">
                <Form.Control
                  as="textarea"
                  rows={2}
                  placeholder="Ask me about your logs... (e.g., 'Show me errors from the last hour')"
                  value={question}
                  onChange={(event) => setQuestion(event.target.value)}
                  onKeyDown={handleQuestionKeyDown}
                  disabled={loading}
                  className="border-0 shadow-sm pe-5"
                  style={{
                    minHeight: "56px",
                    maxHeight: "96px",
                    overflowY: "auto",
                    resize: "none",
                    borderRadius: "12px",
                    background:
                      "linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%)",
                    padding: "16px 50px 16px 20px",
                  }}
                />
                <Button
                  type="submit"
                  disabled={loading || !question.trim()}
                  className="position-absolute border-0 shadow-sm text-white d-flex align-items-center gap-1"
                  style={{
                    right: "8px",
                    top: "50%",
                    transform: "translateY(-50%)",
                    borderRadius: "8px",
                    background:
                      "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
                    border: "none",
                    minWidth: "72px",
                    height: "34px",
                    padding: "0 10px",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                  }}
                >
                  {loading ? (
                    <Spinner size="sm" />
                  ) : (
                    <>
                      <MdSend size={16} />
                      <span>Send</span>
                    </>
                  )}
                </Button>
              </div>
            </Form.Group>

            <div className="d-flex justify-content-between align-items-center mt-3">
              <small className="text-muted d-flex align-items-center">
                <i className="bi bi-info-circle me-1"></i>
                Scans up to {DEFAULT_MAX_LOGS} recent logs per request
              </small>
              <small className="text-muted">
                Press Enter to send, Shift+Enter for new line
              </small>
            </div>
          </Form>
        </div>
      </div>
    </Container>
  );
};

export default Chat;
