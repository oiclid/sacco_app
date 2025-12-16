git filter-branch -f --commit-filter '
GIT_AUTHOR_NAME="oïclid"
GIT_AUTHOR_EMAIL="1678413+oiclid@users.noreply.github.com"
GIT_COMMITTER_NAME="$GIT_AUTHOR_NAME"
GIT_COMMITTER_EMAIL="$GIT_AUTHOR_EMAIL"
git commit-tree "$@" -S
' -- --all
