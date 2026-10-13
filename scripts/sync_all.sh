#!/usr/bin/env bash
# 一键推送本地各仓库到私有远端（ECS 裸库）：飞轮 4 仓 + 治理层 LIBGOV。
#
# 背景：「单一真源」必须有异地备份。本脚本把各仓库一次推完，
#       并自动报告状态，避免"某个仓库忘了推"导致的静默漂移。
#
# 用法：
#   bash sync_all.sh           # 推全部
#   bash sync_all.sh --dry     # 只看状态不推
#
# 远端：ecs:/srv/git/<name>.git（见 ADR-0003）

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

  if [ "$ahead" = "0" ] && [ "$dirty" = "0" ]; then
    echo "                       ↑ 已最新，无需推送"
    continue
  fi

  if [ "$ahead" != "0" ] && [ "$ahead" != "?" ]; then
    if git push -q origin "$branch" 2>&1 | head -3; then
      echo "                       ✅ 推送完成"
    else
      echo "                       ❌ 推送失败"
      fail=1
    fi
  fi

  if [ "$dirty" != "0" ]; then
    echo "                       ⚠️ 有 $dirty 项未提交 —— 本脚本不自动提交，请手工处理"
  fi
done

echo ""
if [ "$fail" = "1" ]; then
  echo "❌ 有仓库推送失败。"
  exit 1
fi
echo "✅ 同步检查完成。"
echo ""
echo "提示：远端在 ECS（异地），本地硬盘损坏也可恢复："
echo "  git clone ecs:/srv/git/<name>.git"
