# Add SSH Key to GitHub - Quick Guide

## Your SSH Public Key

Copy this entire line:

```
ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIA2qHy/O+EQ5styVhPh8DVGI3cmAZBycFo7SLlWX6U/e deanwheatley@hotmail.com
```

## Steps

1. **Open GitHub SSH Keys page:**
   - Go to: https://github.com/settings/keys
   - Or run: `xdg-open https://github.com/settings/keys`

2. **Add the key:**
   - Click the green **"New SSH key"** button
   - Title: Enter any name (e.g., "Linux Laptop", "daemon-breathalyzer")
   - Key: Paste the entire key from above
   - Click **"Add SSH key"**

3. **Verify:**
   - You should see your new key listed

4. **Push your code:**
   ```bash
   cd ~/projects/daemon-breathalyzer
   git push -u origin main
   ```

## Alternative: Copy Key to Clipboard

If you have `xclip` installed:
```bash
cat ~/.ssh/id_ed25519.pub | xclip -selection clipboard
```

Then just paste (Ctrl+V) into the GitHub page.

## Test Connection

After adding the key, test it:
```bash
ssh -T git@github.com
```

You should see: "Hi deanwheatley! You've successfully authenticated..."


