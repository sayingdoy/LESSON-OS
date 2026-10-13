#!/usr/bin/env bash
# 一键推送本地各仓库到远端：飞轮 4 仓 + 治理层 LIBGOV。
#
# 背景：「单一真源」必须有异地备份。本脚本把各仓库一次推完，
#       并自动报告状态，避免"某个仓库忘了推"导致的静默漂移。
#
# 用法：
#   bash sync_all.sh           # 推全部
#   bash sync_all.sh --dry     # 只看状态不推
#
# 远端（**双远端**）：
#   origin = ecs:/srv/git/<name>.git   （自建裸库，异地主副本，见 ADR-0003）
#   github = github.com/sayingdoy/<name>（**私有**，异地第二副本）
#   缺哪个就跳过哪个（`git remote get-url` 探测），不视为失败。

set -u

REPOS=(
  "D:/Projects/LESSON-OS"
  "D:/Projects/LIBGOV"
  "D:/SixSigmaBlackBelt"
  "D:/Projects/vocab-app"
  "D:/Projects/Project AI Kongzi"
)

DRY=0
[ "${1:-}" = "--dry" ] && DRY=1

fail=0
echo "═══ 飞轮同步 → ecs:/srv/git ═══"
echo ""

for p in "${REPOS[@]}"; do
  name="$(basename "$p")"
  if [ ! -d "$p/.git" ]; then
    echo "⚠️  $name: 不是 git 仓库，跳过"
    continue
  fi
  cd "$p" || continue

  branch="$(git branch --show-current)"
  dirty="$(git status --porcelain | wc -l | tr -d ' ')"

  # 未推送的提交数
  ahead="$(git rev-list --count "@{u}..HEAD" 2>/dev/null || echo '?')"

  printf '%-24s 分支=%-7s 未提交=%-4s 待推送=%s\n' "$name" "$branch" "$dirty" "$ahead"

  if [ "$DRY" = "1" ]; then
    continue
  fi

  if [ "$dirty" != "0" ]; then
    echo "                       ⚠️ 有 $dirty 项未提交 —— 本脚本不自动提交，请手工处理"
  fi

  # ── 双远端推送 ────────────────────────────────────────────────────────
  # ⚠️ 教训：不能用 `git push ... | head` 判成败 —— 管道的退出码取自 head
  #    （恒为 0），失败会被吞掉。必须用命令替换捕获 git 的真实退出码。
  # ⚠️ 不再用 `ahead=0` 早退：那只看单一上游（@{u}），github 落后时会被
  #    静默跳过。改为对每个远端**幂等推送**（已最新者秒回 up-to-date）。
  for remote in origin github; do
    if ! git remote get-url "$remote" >/dev/null 2>&1; then
      printf '                       ⏭  %s 未配置，跳过\n' "$remote"
      continue
    fi
    if out="$(git push -q "$remote" "$branch" 2>&1)"; then
      printf '                       ✅ %s 推送完成\n' "$remote"
    else
      printf '                       ❌ %s 推送失败\n' "$remote"
      echo "$out" | head -3 | sed 's/^/                          /'
      fail=1
    fi
  done
done

echo ""
if [ "$fail" = "1" ]; then
  echo "❌ 有仓库推送失败。"
  exit 1
fi
echo "✅ 同步检查完成。"
echo ""
echo "提示：远端在 ECS（异地主）+ GitHub 私有仓（异地次）；本地硬盘损坏也可恢复："
echo "  git clone ecs:/srv/git/<name>.git"
