# GitHub Setup Instructions

## Pushing the Repository to GitHub

1. Go to GitHub.com and create a new repository named 'quizness-partner'

2. Run the following commands to push your repository to GitHub:
   ```bash
   git remote add origin https://github.com/[your-username]/quizness-partner.git
   git push -u origin main
   ```

## Setting Up GitHub Actions CI/CD

1. Once pushed, GitHub will automatically detect the workflow file in `.github/workflows/ci.yml`

2. Enable GitHub Actions in your repository settings if not already enabled

3. To set up GitHub Actions secrets for your OpenAI API key:

   - Go to your repository on GitHub
   - Navigate to Settings > Secrets and variables > Actions
   - Click "New repository secret"
   - Name: `OPENAI_API_KEY`
   - Value: Your OpenAI API key
   - Click "Add secret"

4. Additional secrets you may want to add:
   - `POSTGRES_USER`: Database username
   - `POSTGRES_PASSWORD`: Database password
   - `DOCKER_USERNAME`: For Docker Hub deployments
   - `DOCKER_PASSWORD`: For Docker Hub deployments

## Best Practices for GitHub Collaboration

1. Use feature branches for new development

   ```bash
   git checkout -b feature/new-feature
   ```

2. Create descriptive commit messages

   ```bash
   git commit -m "Add quiz result visualization feature"
   ```

3. Open pull requests for code review before merging to main

4. Set up branch protection rules for the main branch

   - Go to Settings > Branches > Branch protection rules
   - Create a rule for the main branch
   - Enable "Require pull request reviews before merging"
   - Enable "Require status checks to pass before merging"
   - Select the CI checks that must pass

5. Use GitHub Issues to track bugs and feature requests
