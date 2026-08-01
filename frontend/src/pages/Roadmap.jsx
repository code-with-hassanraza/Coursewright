import { useState, useEffect, useCallback } from "react";
import { useParams, Link } from "react-router-dom";
import PageWrapper from "../components/layout/PageWrapper";
import useAuth from "../hooks/useAuth";
import {
  getSpecialization,
  exploreSpecialization,
} from "../services/specializationService";
import {
  getRoadmapBySpecialization,
  getRoadmapById,
} from "../services/roadmapService";
import { getUserProgress } from "../services/userService";
import { getTasksBySpecialization } from "../services/taskService";
import { getQuiz, submitQuiz } from "../services/quizService";
import {
  getMyCertificates,
  generateCertificate,
} from "../services/certificateService";
import { getErrorMessage } from "../utils/errors";
import Chatbot from "../components/chatbot/Chatbot";

const TYPE_BADGE_STYLES = {
  topic: "bg-primary-container/10 text-primary",
  skill: "bg-tertiary-container/10 text-tertiary",
  project: "bg-secondary-container text-on-secondary-container",
  milestone: "border border-ink text-ink",
};

const RESOURCE_ICONS = {
  video: "play_circle",
  article: "article",
  course: "school",
  doc: "description",
  documentation: "description",
  book: "menu_book",
};

function buildChildrenMap(nodes) {
  const byParent = new Map();
  for (const node of nodes) {
    const key = node.parent_id || null;
    if (!byParent.has(key)) byParent.set(key, []);
    byParent.get(key).push(node);
  }
  for (const list of byParent.values()) {
    list.sort((a, b) => a.order - b.order);
  }
  return byParent;
}

function NodeItem({ node, childrenByParent, depth = 0 }) {
  const [isExpanded, setIsExpanded] = useState(depth === 0);
  const children = childrenByParent.get(node.id) || [];
  const hasResources = node.resources && node.resources.length > 0;

  return (
    <div className={depth > 0 ? "ml-lg mt-sm" : "mt-md"}>
      <button
        onClick={() => setIsExpanded((v) => !v)}
        className="flex w-full items-center gap-md rounded-md border border-hairline-soft bg-surface-card p-md text-left"
      >
        {/* Position marker, not a completion indicator — there's no backend
            mechanism to mark an individual roadmap node complete, only tasks. */}
        <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-secondary-bg text-on-secondary">
          <span className="font-body-sm-strong text-body-sm-strong">
            {node.order}
          </span>
        </span>

        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-xs">
            <p className="font-body-strong text-body-strong text-ink">
              {node.title}
            </p>
            <span
              className={`badge ${TYPE_BADGE_STYLES[node.type] || "bg-secondary-bg text-on-secondary"}`}
            >
              {node.type}
            </span>
          </div>
          {node.description && (
            <p className="font-body-sm text-body-sm text-mute">
              {node.description}
            </p>
          )}
        </div>

        {node.estimated_hours ? (
          <span className="shrink-0 font-body-sm text-body-sm text-ash">
            {node.estimated_hours}h
          </span>
        ) : null}
        <span className="material-symbols-outlined shrink-0 text-mute">
          {isExpanded ? "expand_less" : "expand_more"}
        </span>
      </button>

      {isExpanded && (
        <div className="mt-sm">
          {hasResources && (
            <div className="ml-lg flex flex-col gap-xs">
              {node.resources.map((resource, i) => (
                <a
                  key={i}
                  href={resource.url}
                  target="_blank"
                  rel="noreferrer"
                  className="flex items-center gap-xs rounded-md bg-canvas p-sm hover:bg-surface-card"
                >
                  <span className="material-symbols-outlined text-primary">
                    {RESOURCE_ICONS[resource.type] || "link"}
                  </span>
                  <span className="font-body-sm text-body-sm text-ink">
                    {resource.title}
                  </span>
                  {resource.is_free && (
                    <span className="badge bg-primary-container/10 text-body-sm-strong text-primary">
                      Free
                    </span>
                  )}
                </a>
              ))}
            </div>
          )}
          {children.map((child) => (
            <NodeItem
              key={child.id}
              node={child}
              childrenByParent={childrenByParent}
              depth={depth + 1}
            />
          ))}
        </div>
      )}
    </div>
  );
}

export default function Roadmap() {
  const { spec_id } = useParams();
  const { user } = useAuth();

  const [spec, setSpec] = useState(null);
  const [roadmap, setRoadmap] = useState(null);
  const [progress, setProgress] = useState(null);
  const [tasks, setTasks] = useState([]);
  const [quiz, setQuiz] = useState(null);
  const [certificate, setCertificate] = useState(null);
  const [answers, setAnswers] = useState({});
  const [quizResult, setQuizResult] = useState(null);
  const [isSubmittingQuiz, setIsSubmittingQuiz] = useState(false);
  const [quizError, setQuizError] = useState(null);
  const [isGeneratingCert, setIsGeneratingCert] = useState(false);
  const [certError, setCertError] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isStarting, setIsStarting] = useState(false);
  const [chatOpen, setChatOpen] = useState(false);

  const load = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const specData = await getSpecialization(spec_id);
      setSpec(specData);

      let matchedProgress = null;
      if (user?.id) {
        const progressData = await getUserProgress(user.id);
        matchedProgress =
          progressData.items.find((p) => p.specialization_id === spec_id) ||
          null;
      }
      setProgress(matchedProgress);

      const roadmapData = matchedProgress?.roadmap_id
        ? await getRoadmapById(matchedProgress.roadmap_id)
        : await getRoadmapBySpecialization(spec_id);
      setRoadmap(roadmapData);

      const tasksData = await getTasksBySpecialization(spec_id).catch(() => ({
        items: [],
      }));
      setTasks(tasksData.items);

      const quizData = await getQuiz(spec_id);
      setQuiz(quizData);

      if (user?.id) {
        const certs = await getMyCertificates().catch(() => []);
        setCertificate(
          certs.find((c) => c.specialization_id === spec_id) || null,
        );
      }
    } catch (err) {
      setError(getErrorMessage(err, "We couldn't load this roadmap."));
    } finally {
      setIsLoading(false);
    }
  }, [spec_id, user?.id]);

  useEffect(() => {
    load();
  }, [load]);

  async function handleStart() {
    setIsStarting(true);
    try {
      const newProgress = await exploreSpecialization(spec_id, roadmap?.id);
      setProgress(newProgress);
    } catch (err) {
      if (err.response?.status === 400) {
        await load();
      }
    } finally {
      setIsStarting(false);
    }
  }

  async function handleQuizSubmit(e) {
    e.preventDefault();
    setIsSubmittingQuiz(true);
    setQuizError(null);
    try {
      const result = await submitQuiz(quiz.id, answers);
      setQuizResult(result);
    } catch (err) {
      setQuizError(
        getErrorMessage(err, "Unable to submit the quiz. Please try again."),
      );
    } finally {
      setIsSubmittingQuiz(false);
    }
  }

  async function handleGenerateCertificate() {
    setIsGeneratingCert(true);
    setCertError(null);
    try {
      const cert = await generateCertificate(spec_id);
      setCertificate(cert);
    } catch (err) {
      setCertError(
        getErrorMessage(
          err,
          "Unable to generate your certificate. Please try again.",
        ),
      );
    } finally {
      setIsGeneratingCert(false);
    }
  }

  const completedSet = new Set(progress?.completed_nodes || []);
  const totalTasks = tasks.length;
  const completedTaskCount = tasks.filter((t) => completedSet.has(t.id)).length;
  const percent =
    totalTasks > 0 ? Math.round((completedTaskCount / totalTasks) * 100) : 0;
  const childrenByParent = roadmap
    ? buildChildrenMap(roadmap.nodes)
    : new Map();
  const topLevelNodes = childrenByParent.get(null) || [];

  return (
    <>
      <PageWrapper
        isLoading={isLoading}
        error={error}
        onRetry={load}
        maxWidth="max-w-5xl"
      >
        {!roadmap ? (
          <div className="rounded-md border border-hairline-soft bg-surface-card p-xl text-center">
            <p className="font-heading-md text-heading-md text-ink">
              No roadmap published yet
            </p>
            <p className="mt-xs font-body-sm text-body-sm text-mute">
              Check back soon, or explore other specializations in the meantime.
            </p>
            <Link to="/fields" className="btn-primary mt-lg inline-flex">
              Explore Fields
            </Link>
          </div>
        ) : (
          <div>
            <h1 className="font-heading-xl text-heading-xl text-ink">
              {roadmap.title || spec?.name}
            </h1>
            {spec && (
              <p className="mt-xs font-body-sm text-body-sm text-mute">
                {spec.name}
              </p>
            )}

            {!progress ? (
              <div className="mt-lg flex flex-col items-start gap-md rounded-md border border-hairline-soft bg-surface-card p-lg sm:flex-row sm:items-center sm:justify-between">
                <p className="font-body-sm text-body-sm text-ink">
                  You haven't started tracking progress on this path yet.
                </p>
                <button
                  onClick={handleStart}
                  disabled={isStarting}
                  className="btn-primary shrink-0"
                >
                  {isStarting ? "Starting…" : "Start Exploring"}
                </button>
              </div>
            ) : (
              <div className="mt-lg">
                <div className="flex items-center justify-between font-body-sm-strong text-body-sm-strong text-ink">
                  <span>
                    {completedTaskCount} of {totalTasks} tasks complete
                  </span>
                  <span>{percent}%</span>
                </div>
                <div className="mt-xs h-2 w-full overflow-hidden rounded-full bg-secondary-bg">
                  <div
                    className="h-full rounded-full bg-primary transition-all"
                    style={{ width: `${percent}%` }}
                  />
                </div>
              </div>
            )}

            <div className="mt-xl">
              <h2 className="font-heading-lg text-heading-lg text-ink">
                Curriculum
              </h2>
              {topLevelNodes.length === 0 ? (
                <p className="mt-md font-body-sm text-body-sm text-mute">
                  This roadmap doesn't have any content yet.
                </p>
              ) : (
                topLevelNodes.map((node) => (
                  <NodeItem
                    key={node.id}
                    node={node}
                    childrenByParent={childrenByParent}
                  />
                ))
              )}
            </div>

            {tasks.length > 0 && (
              <div className="mt-xl">
                <h2 className="font-heading-lg text-heading-lg text-ink">
                  Practice Tasks
                </h2>
                <div className="mt-md grid gap-md sm:grid-cols-2">
                  {tasks.map((task) => {
                    const taskDone = completedSet.has(task.id);
                    return (
                      <Link
                        key={task.id}
                        to={`/tasks/${task.id}`}
                        className="pin-card custom-shadow-hover flex items-center gap-md p-md"
                      >
                        <span
                          className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full ${
                            taskDone
                              ? "bg-primary text-on-primary"
                              : "bg-secondary-bg text-on-secondary"
                          }`}
                        >
                          <span className="material-symbols-outlined text-base">
                            {taskDone ? "check" : "radio_button_unchecked"}
                          </span>
                        </span>
                        <div className="min-w-0 flex-1">
                          <p className="font-body-strong text-body-strong text-ink">
                            {task.title}
                          </p>
                          <p className="font-body-sm text-body-sm text-mute">
                            {task.difficulty}
                          </p>
                        </div>
                      </Link>
                    );
                  })}
                </div>
              </div>
            )}

            {certificate ? (
              <div className="mt-xl rounded-md border border-hairline-soft bg-surface-card p-xl text-center">
                <span className="material-symbols-outlined text-primary">
                  workspace_premium
                </span>
                <p className="mt-xs font-heading-md text-heading-md text-ink">
                  Certificate Earned
                </p>
                <Link to="/profile" className="btn-outline mt-md inline-flex">
                  View in Profile
                </Link>
              </div>
            ) : (
              quiz && (
                <div className="mt-xl rounded-md border border-hairline-soft bg-surface-card p-xl">
                  <h2 className="font-heading-lg text-heading-lg text-ink">
                    {quiz.title}
                  </h2>

                  {!quizResult ? (
                    <form
                      onSubmit={handleQuizSubmit}
                      className="mt-md flex flex-col gap-lg"
                    >
                      {quiz.questions.map((q, i) => (
                        <div key={q.id}>
                          <p className="font-body-strong text-body-strong text-ink">
                            {i + 1}. {q.question}
                          </p>
                          <div className="mt-sm flex flex-col gap-xs">
                            {q.options.map((option) => (
                              <label
                                key={option}
                                className="flex items-center gap-xs"
                              >
                                <input
                                  type="radio"
                                  name={q.id}
                                  value={option}
                                  checked={answers[q.id] === option}
                                  onChange={() =>
                                    setAnswers((prev) => ({
                                      ...prev,
                                      [q.id]: option,
                                    }))
                                  }
                                  className="accent-primary"
                                />
                                <span className="font-body-sm text-body-sm text-ink">
                                  {option}
                                </span>
                              </label>
                            ))}
                          </div>
                        </div>
                      ))}

                      {quizError && (
                        <p className="rounded-md border border-error-container bg-error-container px-md py-sm font-body-sm text-body-sm text-on-error-container">
                          {quizError}
                        </p>
                      )}

                      <button
                        type="submit"
                        disabled={
                          isSubmittingQuiz ||
                          Object.keys(answers).length < quiz.questions.length
                        }
                        className="btn-primary justify-center"
                      >
                        {isSubmittingQuiz ? "Submitting…" : "Submit Quiz"}
                      </button>
                    </form>
                  ) : (
                    <div className="mt-md">
                      <p
                        className={`font-heading-md text-heading-md ${quizResult.passed ? "text-primary" : "text-error"}`}
                      >
                        {quizResult.score}% —{" "}
                        {quizResult.passed ? "Passed" : "Not passed yet"}
                      </p>
                      <p className="font-body-sm text-body-sm text-mute">
                        {quizResult.correct} of {quizResult.total} correct (pass
                        mark: {quizResult.pass_score}%)
                      </p>

                      <div className="mt-lg flex flex-col gap-md">
                        {quiz.questions.map((q, i) => {
                          const userAnswer = answers[q.id];
                          const wasCorrect = userAnswer === q.correct;
                          return (
                            <div
                              key={q.id}
                              className="rounded-md bg-canvas p-md"
                            >
                              <p className="font-body-strong text-body-strong text-ink">
                                {i + 1}. {q.question}
                              </p>
                              <p
                                className={`mt-xs font-body-sm text-body-sm ${wasCorrect ? "text-primary" : "text-error"}`}
                              >
                                Your answer: {userAnswer || "(none)"}
                                {!wasCorrect &&
                                  ` — correct answer: ${q.correct}`}
                              </p>
                              {q.explanation && (
                                <p className="mt-xs font-body-sm text-body-sm text-mute">
                                  {q.explanation}
                                </p>
                              )}
                            </div>
                          );
                        })}
                      </div>

                      {certError && (
                        <p className="mt-lg rounded-md border border-error-container bg-error-container px-md py-sm font-body-sm text-body-sm text-on-error-container">
                          {certError}
                        </p>
                      )}

                      {quizResult.passed ? (
                        <button
                          onClick={handleGenerateCertificate}
                          disabled={isGeneratingCert}
                          className="btn-primary mt-lg justify-center"
                        >
                          {isGeneratingCert
                            ? "Generating…"
                            : "Generate Certificate"}
                        </button>
                      ) : (
                        <button
                          onClick={() => {
                            setQuizResult(null);
                            setAnswers({});
                          }}
                          className="btn-secondary mt-lg justify-center"
                        >
                          Try Again
                        </button>
                      )}
                    </div>
                  )}
                </div>
              )
            )}
          </div>
        )}
      </PageWrapper>

      {roadmap && (
        <>
          <button
            onClick={() => setChatOpen((v) => !v)}
            className="fixed bottom-xl right-xl z-20 flex h-14 w-14 items-center justify-center rounded-full bg-primary text-on-primary shadow-xl hover:bg-primary-pressed"
            aria-label="Open learning assistant"
          >
            <span className="material-symbols-outlined">
              {chatOpen ? "close" : "smart_toy"}
            </span>
          </button>

          <Chatbot
            specializationId={spec_id}
            roadmapId={roadmap?.id}
            isOpen={chatOpen}
            onClose={() => setChatOpen(false)}
          />
        </>
      )}
    </>
  );
}
