# Stage 1 - Minimal chat (video 01:19 - 02:52)

> "The first thing that we're going to do is just create a minimal chat
> application."

One file, `llm.py`. It asks for a prompt, sends a system message and a user
message, prints the reply and the usage numbers.

```
you ──▶ [system, user] ──▶ model ──▶ content ──▶ printed
                                     usage   ──▶ printed
```

## What the video sets up here

- **Credentials from the environment.** `BASE_URL` and `API_KEY`. The
  video points them at OpenRouter and uses `deepseek/deepseek-v4-flash`,
  "one of the fastest as well as cheapest models". Any OpenAI-compatible
  endpoint works; `MODEL` overrides the model id.
- **Two messages.** `system` carries the prompt ("You are a coding agent.
  Your job is to code. Always code."), `user` carries what you typed.
- **Usage from the very first call.** Prompt tokens, completion tokens,
  reasoning tokens and cached tokens. The cached number is the one to watch
  from stage 2.4 onward.

## Run it

```bash
export BASE_URL=https://openrouter.ai/api/v1 API_KEY=sk-or-...
python llm.py
Enter your prompt> hi
```

"Very simple, very easy and this is the most basic step, but trust me this
is one of the most important steps."

## Next

Stage 2.1 gives the model a tool. Ask this version "what is your current
directory?" and it can only guess.
