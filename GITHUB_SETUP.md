# GitHub 仓库设置指南

## 当前状态

代码已经完成初始提交并准备好推送到GitHub。

## 添加远程仓库

请提供您的 GitHub 用户名，然后运行以下命令（将 `YOUR_USERNAME` 替换为您的GitHub用户名）：

### HTTPS方式（推荐，适合大多数用户）

```bash
git remote add origin https://github.com/YOUR_USERNAME/RadioPotato.git
git push -u origin main
```

### SSH方式（如果您已配置SSH密钥）

```bash
git remote add origin git@github.com:YOUR_USERNAME/RadioPotato.git
git push -u origin main
```

## 如果没有提供用户名

如果您已经知道完整的仓库URL，可以直接使用：

```bash
git remote add origin <您的仓库URL>
git push -u origin main
```

## 首次推送后

1. 访问 https://github.com/YOUR_USERNAME/RadioPotato 查看您的仓库
2. 可以添加 README.md 中的描述
3. 可以添加 Topics 标签，例如：`python`, `audio-player`, `scheduler`, `tkinter`, `windows`

## 后续更新代码

如果代码有更新，使用以下命令：

```bash
git add .
git commit -m "更新描述"
git push
```

