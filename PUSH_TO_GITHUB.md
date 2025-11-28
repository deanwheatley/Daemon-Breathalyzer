# Pushing to GitHub

## Current Status

Your repository is set up with the remote URL:
```
https://github.com/deanwheatley/daemon-breathalyzer.git
```

## To Push Your Code

### Option 1: Using Personal Access Token (Recommended)

1. **Create a Personal Access Token on GitHub:**
   - Go to: https://github.com/settings/tokens
   - Click "Generate new token" → "Generate new token (classic)"
   - Give it a name: "daemon-breathalyzer"
   - Select scopes: ✅ `repo` (all repo permissions)
   - Click "Generate token"
   - **Copy the token** (you won't see it again!)

2. **Push using the token:**
   ```bash
   cd ~/projects/daemon-breathalyzer
   git push -u origin main
   ```
   
   When prompted:
   - **Username**: `deanwheatley`
   - **Password**: Paste your Personal Access Token (not your GitHub password)

### Option 2: Using GitHub CLI

If you have GitHub CLI installed:

```bash
# Authenticate (first time only)
gh auth login

# Push your code
git push -u origin main
```

### Option 3: Set Up SSH Keys (Most Secure Long-term)

1. **Generate SSH key:**
   ```bash
   ssh-keygen -t ed25519 -C "your_email@example.com"
   # Press Enter to accept default location
   # Optionally set a passphrase
   ```

2. **Add SSH key to ssh-agent:**
   ```bash
   eval "$(ssh-agent -s)"
   ssh-add ~/.ssh/id_ed25519
   ```

3. **Copy your public key:**
   ```bash
   cat ~/.ssh/id_ed25519.pub
   ```

4. **Add to GitHub:**
   - Go to: https://github.com/settings/keys
   - Click "New SSH key"
   - Paste your public key
   - Click "Add SSH key"

5. **Change remote to SSH:**
   ```bash
   cd ~/projects/daemon-breathalyzer
   git remote set-url origin git@github.com:deanwheatley/daemon-breathalyzer.git
   ```

6. **Push:**
   ```bash
   git push -u origin main
   ```

## Troubleshooting

### If you get "Repository not found":
- Make sure the repository exists at: https://github.com/deanwheatley/daemon-breathalyzer
- If it doesn't exist, create it on GitHub first

### If you get authentication errors:
- Make sure your username is correct: `deanwheatley`
- For HTTPS: Use a Personal Access Token, not your password
- For SSH: Make sure your SSH key is added to GitHub

### Quick Push Command:

Once authenticated, you can simply run:
```bash
cd ~/projects/daemon-breathalyzer
git push -u origin main
```

The `-u` flag sets up tracking so future pushes can be done with just `git push`.


