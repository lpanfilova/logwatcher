import {
  useEffect,
  useRef,
  useState,
  type FormEvent,
  type KeyboardEvent,
} from "react";
import { Button, Card, Container, Form, Spinner } from "react-bootstrap";
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

  const handleQuestionKeyDown = (
    event: KeyboardEvent<HTMLTextAreaElement>,
  ) => {
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
              ul: ({ node, ...props }) => <ul className="mb-3 ps-4" {...props} />,
              ol: ({ node, ...props }) => <ol className="mb-3 ps-4" {...props} />,
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
      <div className="shadow rounded border bg-white mb-4 p-3">
        <h3 className="text-center mb-1">Chat</h3>
        <p className="text-center text-muted mb-0">
          Ask the AI backend questions about recent logs.
        </p>
      </div>

      <Card className="shadow-sm border-0 flex-grow-1 d-flex flex-column overflow-hidden">
        <Card.Body
          ref={transcriptRef}
          className="d-flex flex-column gap-3 overflow-auto"
          style={{ backgroundColor: "#f8f9fa" }}
        >
          {messages.length === 0 ? (
            <div className="text-center text-muted my-auto">
              Start the conversation by asking about recent logs.
            </div>
          ) : (
            messages.map((message) => (
              <div
                key={message.id}
                className={`d-flex ${
                  message.role === "user" ? "justify-content-end" : "justify-content-start"
                }`}
              >
                <div
                  className={`rounded-4 px-3 py-2 shadow-sm ${
                    message.role === "user"
                      ? "bg-primary text-white"
                      : message.status === "error"
                        ? "bg-danger-subtle border border-danger"
                        : "bg-white"
                  }`}
                  style={{
                    maxWidth: "75%",
                    whiteSpace: "pre-wrap",
                  }}
                >
                  {message.role === "user" ? (
                    <div style={{ wordBreak: "break-word" }}>{message.content}</div>
                  ) : (
                    renderAssistantMessage(message)
                  )}
                </div>
              </div>
            ))
          )}
        </Card.Body>

        <Card.Body>
          <Form onSubmit={handleSubmit}>
            <Form.Group controlId="chatQuestion">
              <Form.Control
                as="textarea"
                rows={2}
                placeholder="Example: Summarize errors in the last 10 minutes"
                value={question}
                onChange={(event) => setQuestion(event.target.value)}
                onKeyDown={handleQuestionKeyDown}
                disabled={loading}
                style={{
                  minHeight: "56px",
                  maxHeight: "96px",
                  overflowY: "auto",
                  resize: "none",
                }}
              />
            </Form.Group>

            <div className="d-flex justify-content-between align-items-center mt-3">
              <small className="text-muted">
                Scans up to {DEFAULT_MAX_LOGS} recent logs per request.
              </small>
              <Button type="submit" disabled={loading || !question.trim()}>
                {loading ? (
                  <>
                    <Spinner size="sm" className="me-2" />
                    Asking...
                  </>
                ) : (
                  "Ask"
                )}
              </Button>
            </div>
          </Form>
        </Card.Body>
      </Card>
    </Container>
  );
};

export default Chat;
