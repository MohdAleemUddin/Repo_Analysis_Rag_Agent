# Getting repo_analysis_rag/Zeroui_Repo_Analysis_Rag_Agent on your machine

This folder is a **Git submodule**. After you pull the `Confluence-agents` branch, run these commands from the **repo root** (where you see `repo_analysis_rag`, `tests`, `offline-folder-rag`, etc.):

## One-time (after clone or first pull of Confluence-agents)

```powershell
git pull origin Confluence-agents
git submodule update --init --recursive
```

## If you already cloned and the folder is empty

From the repo root:

```powershell
git submodule update --init --recursive
```

That will clone the submodule and check out the correct commit so `repo_analysis_rag/Zeroui_Repo_Analysis_Rag_Agent` is no longer empty.

## Every time you pull and want latest submodule too

```powershell
git pull origin Confluence-agents
git submodule update --init --recursive
```

Or in one go when cloning fresh:

```powershell
git clone --recurse-submodules -b Confluence-agents https://github.com/MohdAleemUddin/Repo_Analysis_Rag_Agent.git
cd Repo_Analysis_Rag_Agent
```
