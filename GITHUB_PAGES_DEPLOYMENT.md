# GitHub Pages Deployment Guide

This guide will walk you through deploying the Energy Sector Security Operations Dashboard to GitHub Pages.

## Prerequisites

- A GitHub account
- Git installed on your local machine
- This repository cloned or forked to your GitHub account

## Step-by-Step Deployment Instructions

### Step 1: Push Your Code to GitHub

If you haven't already, push this repository to GitHub:

```bash
# Initialize git repository (if not already done)
git init

# Add all files
git add .

# Commit your changes
git commit -m "Initial commit: Energy Sector SOC Dashboard"

# Add your GitHub repository as remote
# Replace YOUR_USERNAME and YOUR_REPO with your actual GitHub username and repository name
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git

# Push to GitHub
git push -u origin main
```

### Step 2: Enable GitHub Pages

1. Go to your repository on GitHub
2. Click on **Settings** (top right)
3. In the left sidebar, click on **Pages**
4. Under "Build and deployment":
   - **Source**: Select "GitHub Actions"
5. Click **Save**

### Step 3: Configure GitHub Actions Permissions

1. Still in **Settings**, click on **Actions** in the left sidebar
2. Click on **General**
3. Scroll down to "Workflow permissions"
4. Select **"Read and write permissions"**
5. Check **"Allow GitHub Actions to create and approve pull requests"**
6. Click **Save**

### Step 4: Generate and Deploy

#### Option A: Automatic Deployment (Recommended)

The GitHub Actions workflow is already configured. Simply push to the `main` or `master` branch:

```bash
# Make any changes to your code
git add .
git commit -m "Update dashboard"
git push
```

The workflow will automatically:
1. Generate the static HTML from the template
2. Deploy it to GitHub Pages
3. Make it available at `https://YOUR_USERNAME.github.io/YOUR_REPO/`

#### Option B: Manual Deployment (Local Generation)

If you prefer to generate the static site locally:

```bash
# Install Python dependencies
pip install jinja2

# Generate static site
python generate_static.py

# Add and commit the generated files
git add docs/
git commit -m "Add generated static site"
git push
```

Then configure GitHub Pages to use the `/docs` folder:
1. Go to **Settings** > **Pages**
2. Under "Build and deployment":
   - **Source**: Select "Deploy from a branch"
   - **Branch**: Select "main" and "/docs" folder
3. Click **Save**

### Step 5: Access Your Dashboard

After deployment completes (usually 1-3 minutes):

1. Go to **Settings** > **Pages**
2. You'll see a message: "Your site is live at `https://YOUR_USERNAME.github.io/YOUR_REPO/`"
3. Click the link to view your dashboard!

### Step 6: Monitor Deployment

To check the status of your deployment:

1. Go to the **Actions** tab in your repository
2. Click on the latest workflow run
3. Watch the build and deploy process
4. Once complete, your site will be live!

## Troubleshooting

### Workflow Not Running?

- Check that the workflow file is in `.github/workflows/deploy-pages.yml`
- Ensure you've pushed to the `main` or `master` branch
- Verify GitHub Actions is enabled in your repository settings

### 404 Error?

- Wait a few minutes for DNS propagation
- Check that GitHub Pages is enabled in Settings > Pages
- Verify the `docs` folder contains `index.html`

### Permission Errors?

- Ensure workflow permissions are set to "Read and write permissions"
- Check that Pages permissions are enabled (Settings > Actions > General)

### Build Fails?

- Check the Actions tab for error messages
- Verify Python dependencies are correct
- Ensure `generate_static.py` runs without errors locally

## Customization

### Update Dashboard Data

Edit the `SAMPLE_TRIAGE` list in `generate_static.py` to customize:
- Alert descriptions
- Severity levels
- Evidence details
- User names and locations

Then regenerate:

```bash
python generate_static.py
git add docs/
git commit -m "Update dashboard data"
git push
```

### Modify Styling

Edit `web/templates/dashboard.html`:
- Change colors in the `:root` CSS variables
- Modify layout and components
- Update icons and styling

Then regenerate the static site.

### Change Alert Types

Add new alert types by:
1. Creating new alert objects in `SAMPLE_TRIAGE`
2. Following the existing structure
3. Setting appropriate severity levels

## Notes

### Static vs Dynamic

This GitHub Pages deployment is **static** (read-only):
- ✓ Perfect for demos and portfolios
- ✓ No server costs
- ✓ Fast loading
- ✗ No real-time updates
- ✗ No analyst feedback submission

For a **dynamic** version with real-time features, use the Docker deployment:

```bash
docker-compose up
```

### Security

This demo contains sample data only. Never deploy:
- Real IP addresses
- Actual user credentials
- Sensitive security information
- Production system details

## Support

If you encounter issues:
1. Check the [GitHub Pages documentation](https://docs.github.com/en/pages)
2. Review the [GitHub Actions logs](https://docs.github.com/en/actions)
3. Ensure all files are committed and pushed

## License

This project is provided as-is for demonstration and educational purposes.
