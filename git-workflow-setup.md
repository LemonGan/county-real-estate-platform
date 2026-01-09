# Git分支管理和工作流指南

## 1. Git工作流策略

### 1.1 分支模型（简化版GitFlow）
```
main                    # 生产分支 - 稳定版本 ✨
├── dev                 # 开发分支 - 集成功能 💡
├── feature/*           # 功能分支 - 新功能开发 🔥
├── hotfix/*            # 热修复 - 紧急生产修复 🚑
└── release/*           # 发布分支 - 版本发布准备 🚀
```

### 1.2 分支说明

| 分支类型 | 命名规范 | 用途 | 生命周期 |
|---------|---------|------|----------|
| main | main | 生产环境稳定代码 | 永久 |
| dev | dev | 开发集成和功能测试 | 永久 |
| feature | feature/功能名 | 新功能开发 | 功能完成 |
| hotfix | hotfix/问题描述 | 生产环境紧急修复 | 修复后立即删除 |
| release | release/v版本号 | 发布前准备（文档、版本号） | 发布完成后删除 |

## 2. 分支创建和管理

### 2.1 初始化分支结构
```bash
# 在本地初始化Git仓库
git init

# 创建初始提交
echo "# 县域房产信息平台" > README.md
git add README.md
git commit -m "Initial commit 🎉"

# 创建开发分支
git checkout -b dev
git push -u origin dev

# 返回主分支
git checkout main
```

### 2.2 功能分支工作流程

#### Step 1: 开始新功能开发
```bash
# 确保你在dev分支上
git checkout dev
git pull origin dev  # 同步最新代码

# 创建功能分支
git checkout -b feature/user-authentication
git push -u origin feature/user-authentication
```

#### Step 2: 功能开发
```bash
# 开发过程中要频繁提交
git add .
git commit -m "feat(auth): add user login endpoint

- Implement JWT-based authentication
- Add password hashing with bcrypt
- Add user login validation"

# 定期推送到远程
git push origin feature/user-authentication
```

#### Step 3: 集成测试前的准备
```bash
# 功能完成后，先合并最新的dev分支
git checkout dev
git pull origin dev
git checkout feature/user-authentication
git merge dev

# 解决可能的冲突
git add .
git commit -m "merge dev into feature/user-authentication"
```

#### Step 4: Pull Request创建
```bash
# 推送到远程然后创建PR
git push origin feature/user-authentication

# 在GitHub上创建PR，目标分支设为dev
```

#### Step 5: 代码审查和合并
```bash
# 根据review意见修改
git add .
git commit -m "fix(auth): address code review comments

- Improve error handling in login function
- Add validation for phone number format
- Update docstrings"
git push origin feature/user-authentication

# PR合并后删除功能分支
git checkout dev
git branch -d feature/user-authentication
git push origin --delete feature/user-authentication
```

## 3. 提交规范（Conventional Commits）

### 3.1 提交格式
```
<type>(<scope>): <subject>

<body>

<footer>
```

### 3.2 提交类型

| 类型 | 描述 | 示例 |
|------|------|------|
| feat | 新功能 | feat: add user registration with phone verification |
| fix | Bug修复 | fix: correct filter logic in property search |
| docs | 文档更新 | docs: update API documentation for authentication |
| style | 代码格式 | style: reformat Python code with black |
| refactor | 代码重构 | refactor: improve database query performance |
| perf | 性能优化 | perf: add Redis caching for property listing |
| test | 测试相关 | test: add unit tests for user authentication |
| build | 构建相关 | build: update Docker configuration |
| ci | CI/CD | ci: update GitHub Actions workflow |
| chore | 杂项 | chore: update dependencies |
| revert | 回退 | revert: revert previous commit that broke CI |

### 3.3 提交示例

#### 正确的提交信息
```bash
# 好的示例
git commit -m "feat(authentication): add WeChat MiniProgram login integration

- Implement getPhoneNumber API handling
- Add JWT token refresh mechanism
- Update user model to store encrypted phone number

Closes #23"

git commit -m "fix(property): resolve pagination issue in property listing

- Fix offset calculation for page > 1
- Add missing page size validation
- Update tests to cover edge cases"

git commit -m "perf(cache): improve property search performance

- Add Redis caching for filtered results
- Implement cache invalidation on property update
- Reduce average response time by 60%"
```

#### 避免的提交信息
```bash
# ❌ 不好的示例
git commit -m "update code"
# ❌ 太模糊，没有描述具体更改
git commit -m "fix"
# ❌ 没有说明修复了什么gigit commit -m "update stuff"

# ❌ 过于简单，没有意义
```

## 4. 分支命名规范

### 4.1 功能分支
```bash
# 格式: feature/功能描述
git checkout -b feature/user-authentication
git checkout -b feature/property-search-filtering
git checkout -b feature/mortgage-calculator
```

### 4.2 Bug修复分支
```bash
# 格式: bugfix/问题描述
git checkout -b bugfix/login-validation-error
git checkout -b bugfix/property-image-upload-filing
```

### 4.3 热修复分支
```bash
# 格式: hotfix/紧急修复描述
git checkout -b hotfix/critical-security-patch
git checkout -b hotfix/production-api-crash
```

### 4.4 发布分支
```bash
# 格式: release/v版本号
git checkout -b release/v0.2.0
git checkout -b release/v1.0.0
```

## 5. 合并策略

### 5.1 功能分支到开发分支（Squash Merge）
```bash
# 在GitHub Web界面选择 Squash and Merge\n# 或者在主分支上操作\ngit checkout dev\ngit merge --squash feature/user-authentication\ngit commit -m "feat(auth): implement user authentication system\n\n- Add phone verification during registration\n- Implement JWT-based login\n- Add password reset functionality\n- Include comprehensive unit tests\n\nCloses #45"