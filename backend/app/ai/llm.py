import json
import logging
from typing import Dict, Any, List, Optional, Union
from app.core.config import settings
from app.ai.prompts import SYSTEM_EXPLAINER_PROMPT, CHAT_COMPANION_PROMPT
from app.schemas.ai import AIContext

logger = logging.getLogger(__name__)


class LLMService:
    """
    Handles communication with Groq LLM API, with strict evidence grounding
    and deterministic, compassionate fallbacks.
    """

    def __init__(self):
        self.api_key = settings.GROQ_API_KEY
        self.model_name = settings.GROQ_MODEL
        self.client = None
        if self.api_key:
            try:
                from groq import Groq
                self.client = Groq(api_key=self.api_key)
            except Exception as e:
                logger.warning(f"Could not initialize Groq Client: {e}")

    def _normalize_context(self, context: Union[Dict[str, Any], AIContext]) -> Dict[str, Any]:
        """Converts AIContext or dictionary to a clean serializable dict."""
        if isinstance(context, AIContext):
            return context.to_dict()
        return context

    def generate_explanation(
        self,
        context: Union[Dict[str, Any], AIContext],
        question: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Generates a data-backed behavioral explanation and micro-experiment."""
        context_dict = self._normalize_context(context)

        # Safe development observability
        logger.debug(
            f"Building AI explanation: intents={context_dict.get('classified_intents')}, "
            f"metrics_keys={list(context_dict.get('metrics', {}).keys())}, "
            f"pattern_count={len(context_dict.get('patterns', []))}, "
            f"experiment_count={len(context_dict.get('experiments', []))}"
        )

        if self.client:
            try:
                system_content = (
                    f"{SYSTEM_EXPLAINER_PROMPT}\n\n"
                    f"VERIFIED USER BEHAVIORAL EVIDENCE (STRUCTURED CONTEXT):\n"
                    f"{json.dumps(context_dict, indent=2)}"
                )
                user_content = question or "Explain my productivity patterns and suggest a micro-experiment to test."
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[
                        {"role": "system", "content": system_content},
                        {"role": "user", "content": user_content},
                    ],
                )
                text = response.choices[0].message.content or ""
                return {
                    "title": "Behavioral Insight & Next Experiment",
                    "explanation": text,
                    "deterministic_context": context_dict,
                    "suggested_micro_experiment": "See explanation above for proposed micro-experiment.",
                    "tone": "compassionate_analytical",
                }
            except Exception as e:
                logger.error(f"Error calling Groq API: {e}")

        # Deterministic zero-shame, question-relevant fallback when offline or no API key provided
        return self._generate_fallback_explanation(context_dict, question)

    def generate_chat_reply(
        self,
        messages: List[Dict[str, str]],
        context: Union[Dict[str, Any], AIContext],
    ) -> str:
        """Generates companion conversational response."""
        context_dict = self._normalize_context(context)

        # Safe development observability
        logger.debug(
            f"Generating companion chat reply: messages_count={len(messages)}, "
            f"intents={context_dict.get('classified_intents')}"
        )

        if self.client:
            try:
                system_content = (
                    f"{CHAT_COMPANION_PROMPT}\n\n"
                    f"Verified User Evidence (Structured AI Context):\n"
                    f"{json.dumps(context_dict, indent=2)}"
                )
                api_messages = [{"role": "system", "content": system_content}]
                for m in messages:
                    api_messages.append({
                        "role": m.get("role", "user"),
                        "content": m.get("content", ""),
                    })

                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=api_messages,
                )
                if response.choices and response.choices[0].message.content:
                    return response.choices[0].message.content.strip()
            except Exception as e:
                logger.error(f"Error in chat reply from Groq: {e}")

        # Empathetic, grounded local fallback
        return self._generate_fallback_chat_reply(messages, context_dict)

    def _generate_fallback_explanation(
        self,
        context: Dict[str, Any],
        question: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Provides an empathetic, mathematically accurate fallback when API key is not active."""
        metrics = context.get("metrics", {})
        comp = metrics.get("task_completion", {})
        delay = metrics.get("start_delay", {})
        patterns = context.get("patterns", [])
        experiments = context.get("experiments", [])
        intents = context.get("classified_intents", [])

        comp_rate = int(comp.get("completion_rate", 0) * 100)
        total_tasks = comp.get("total_tasks_tracked", 0)
        avg_delay = delay.get("average_start_delay_minutes", 0)

        # Question-relevant explanation generation
        if "experiment_evaluation" in intents and experiments:
            exp = experiments[0]
            exp_title = exp.get("title", "Recent Experiment")
            results = exp.get("results", [])
            if results:
                res = results[0]
                text = (
                    f"### Observation\n"
                    f"Looking at your tracked experiment **'{exp_title}'**, the target metric was `{exp.get('target_metric')}`. "
                    f"The recorded baseline was **{res.get('before_value')}**, and the measured outcome was **{res.get('after_value')}** "
                    f"({'+' if (res.get('percent_change') or 0) > 0 else ''}{res.get('percent_change')}% shift). "
                    f"Outcome status is evaluated as **{res.get('conclusion')}**.\n\n"
                    f"### Possible Explanation\n"
                    f"The tested intervention (`{exp.get('intervention_type')}`) directly impacted the initiation loop. "
                    f"{res.get('result_summary')}\n\n"
                    f"### Suggested Next Step\n"
                    f"Based on this data, consider extending this habit for another 3 days or refining the friction boundary."
                )
            else:
                text = (
                    f"### Observation\n"
                    f"Your active experiment **'{exp_title}'** is currently ongoing (target: `{exp.get('target_metric')}`, "
                    f"baseline: {exp.get('baseline_value')}).\n\n"
                    f"### Possible Explanation\n"
                    f"Hypothesis: *\"{exp.get('hypothesis')}\"*\n\n"
                    f"### Suggested Micro-Experiment\n"
                    f"Continue logging your sessions over the remaining cycle so the backend evaluator can measure the shift."
                )
            return {
                "title": f"Experiment Analysis: {exp_title}",
                "explanation": text,
                "deterministic_context": context,
                "suggested_micro_experiment": "Continue current cycle to gather conclusive sample size.",
                "tone": "compassionate_analytical",
            }

        if "evening_performance" in metrics:
            eve = metrics["evening_performance"]
            eve_rate = int(eve.get("completion_rate", 0) * 100)
            text = (
                f"### Observation\n"
                f"Looking at your tracked sessions, your evening task completion rate is **{eve_rate}%** "
                f"across {eve.get('total_tasks', 0)} scheduled evening tasks (compared to overall average of {comp_rate}%).\n\n"
                f"### Possible Explanation\n"
                f"Evening focus drops often stem from accumulated decision fatigue rather than lack of willpower. "
                f"By nightfall, cognitive resistance to task initiation naturally rises.\n\n"
                f"### Suggested Micro-Experiment: Evening Pre-Staging\n"
                f"Try setting up tomorrow evening's materials before dinner, or schedule evening work in a low-friction 15-minute chunk."
            )
            return {
                "title": "Evening Friction Observation",
                "explanation": text,
                "deterministic_context": context,
                "suggested_micro_experiment": "Pre-stage evening task materials earlier in the day.",
                "tone": "compassionate_analytical",
            }

        # Default behavioral pattern observation
        pattern_name = patterns[0]["title"] if patterns else "Task Initiation Inertia"
        text = (
            f"### Observation\n"
            f"Over your {total_tasks} tracked task sessions, your task completion rate is **{comp_rate}%** "
            f"with an average start latency of **{avg_delay} minutes**.\n\n"
            f"### Possible Explanation\n"
            f"Rather than a character flaw or lack of discipline, this reflects natural initiation friction ({pattern_name}): "
            f"the mental barrier between deciding to start and executing the very first step.\n\n"
            f"### Suggested Micro-Experiment: The 5-Minute Gateway\n"
            f"Commit to working on your scheduled task for just **5 minutes** with no obligation to finish. "
            f"If after 5 minutes you wish to stop, you are free to do so. We will measure if this reduces your start delay."
        )

        return {
            "title": "Initial Focus Latency & Gateway Experiment",
            "explanation": text,
            "deterministic_context": context,
            "suggested_micro_experiment": "Commit to just 5 minutes of low-pressure start for the next 3 days.",
            "tone": "compassionate_analytical",
        }

    def _generate_fallback_chat_reply(
        self,
        messages: List[Dict[str, str]],
        context: Dict[str, Any],
    ) -> str:
        """Grounded conversational fallback for companion chat."""
        last_message = messages[-1]["content"].lower() if messages else ""
        metrics = context.get("metrics", {})
        comp = metrics.get("task_completion", {})
        delay = metrics.get("start_delay", {})
        experiments = context.get("experiments", [])
        trajectory = metrics.get("trajectory", {})

        if "experiment" in last_message:
            if experiments:
                exp = experiments[0]
                results = exp.get("results", [])
                if results:
                    r = results[0]
                    return (
                        f"Looking at your experiment '{exp.get('title')}', the outcome was evaluated as "
                        f"{r.get('conclusion')} ({r.get('before_value')} → {r.get('after_value')}). "
                        f"Your backend measured: {r.get('result_summary')}"
                    )
                else:
                    return (
                        f"You have an ongoing experiment: '{exp.get('title')}' focusing on {exp.get('target_metric')}. "
                        f"Keep logging your sessions so we can evaluate the measurable shift!"
                    )
            return "You don't have an active experiment recorded right now. We can create a 3-day micro-experiment anytime!"

        if "improv" in last_message or "progress" in last_message or "better" in last_message:
            score = trajectory.get("improvement_score", 50.0)
            consistency = trajectory.get("consistency_score", 50.0)
            comp_rate = int(comp.get("completion_rate", 0) * 100)
            return (
                f"Your data shows steady momentum: an overall completion rate of {comp_rate}% "
                f"and an improvement trajectory rating of {score}/100 with {consistency}% consistency. "
                f"Remember, progress in FocusLoop is measured in small, repeatable rhythms."
            )

        if "procrastinat" in last_message or "delay" in last_message or "stuck" in last_message:
            raw_delay = delay.get("average_start_delay_minutes")
            if raw_delay is not None:
                delay_sentence = f"Across your sessions, your average start delay is around {raw_delay} minutes."
            else:
                delay_sentence = "You have no recorded initiation delay data yet."
            return (
                f"I hear you. Initiation resistance is completely normal. {delay_sentence} Often, the friction isn't the task itself, but starting. "
                f"Could you try doing just the first 2 minutes right now, with zero pressure to finish?"
            )

        if "thank" in last_message:
            return "You're very welcome! Let's keep treating each day as an empirical experiment rather than a judgment."

        return (
            f"Thanks for sharing that. Looking at your verified focus records ({comp.get('total_tasks_tracked', 0)} sessions tracked), "
            f"you have tangible momentum. How would you like to structure your next focus block?"
        )


llm_service = LLMService()
