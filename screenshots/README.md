# Screenshots

Naming: `flaw-N-before-M.png` / `flaw-N-after-M.png`

| File | Shows |
|------|--------|
| flaw-1-before-1.png | bob reading alice's private note (IDOR) |
| flaw-1-before-2.png | bob on alice's edit form |
| flaw-1-after-1.png | bob gets 403 after access check |
| flaw-2-before-1.png | `notes_member.password` plaintext |
| flaw-2-after-1.png | passwords stored as PBKDF2 hashes |
| flaw-3-before-1.png | search `' OR 1=1 --` returns all notes |
| flaw-3-after-1.png | same payload returns no results |
| flaw-4-before-1.png | register accepts password `1` |
| flaw-4-before-2.png | many failed logins still allowed |
| flaw-4-before-3.png | session cookie without HttpOnly |
| flaw-4-after-1.png | weak password rejected by validators |
| flaw-4-after-2.png | lockout / HTTP 429 after failures |
| flaw-4-after-3.png | HttpOnly / SameSite after fix |
| flaw-5-before-1.png | no `security.log` after failed logins |
| flaw-5-after-1.png | `security.log` with denied/failed events |
