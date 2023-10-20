# AskSJTU | 交大智讯

## 项目简介

本项目是基于 [langchain-chatchat](https://github.com/chatchat-space/Langchain-Chatchat/) 项目的知识库问答工具，在原项目的基础上新增了多用户、知识库管理和部分命令行管理功能。

## 使用方法

### 依赖安装及初始化

项目部署前需要先安装 Langchain-chatchat 项目的依赖，安装方式参考原项目的 [README](./README.md)。除原项目需要的环境外，本项目还需要安装其他依赖，命令总结如下：

```bash
# 安装 langchain-chatchat 项目的依赖
pip install -r requirements.txt
pip install -r requirements_api.txt
pip install -r requirements_webui.txt
# 安装本项目需要的额外依赖
pip install -r requirements_asksjtu.txt
```

依赖安装完成后需要创建配置文件，命令总结如下：

```bash
cp configs/asksjtu_config.py.example configs/asksjtu_config.py
cp configs/basic_config.py.example configs/basic_config.py
cp configs/model_config.py.example configs/model_config.py
cp configs/kb_config.py.example configs/kb_config.py
cp configs/prompt_config.py.example configs/prompt_config.py
cp configs/server_config.py.example configs/server_config.py
```

配置完成后需要进行数据库的初始化，Langchain-Chatchat 项目相关的知识库初始化可以参考 [README](./README.md)，命令总结如下：

```bash
# 初始化向量数据库
python init_database.py --recreate-vs
# 初始化本项目数据库
python asksjtu_cli.py db create
# 将向量数据库相关信息同步到本项目数据库
python asksjtu_cli.py db sync
```

### 部署及运行

Langchain-chatchat 项目提供了无需验证的知识库管理面板，本项目不推荐在生产环境下使用，启动时加上 `--all-api` 选项：

```bash
python startup.py --all-api
```

本项目为普通用户和管理员提供了不同的 WebUI 入口，运行命令如下：

```bash
# 启动普通用户 WebUI
streamlit run asksjtu-webui.py
# 启动管理员 WebUI
streamlit run asksjtu-admin.py
```

## CLI 管理

### Database

支持数据库的创建功能，命令总结如下：

```bash
python asksjtu_cli.py db create
```

### User

支持用户的创建、修改密码、修改权限等功能，命令总结如下：

```bash
python asksjtu_cli.py user create --username <username> --role <role>
python asksjtu_cli.py user reset-password --username <username>
python asksjtu_cli.py user update --username <username> --role <role>
python asksjtu_cli.py user add-kb --username <username> --kb-name <kb-name>
python asksjtu_cli.py user remove-kb --username <username> --kb-name <kb-name>
```

### KnowledgeBase

支持知识库的修改、同步等功能，命令总结如下：

```bash
python asksjtu_cli.py kb sync
python asksjtu_cli.py kb update --kb-name <kb-name> --slug <slug>
```

## Contributors

- [@truc0](https://github.com/truc0) - 项目维护者 【CLI、WebUI、知识库、语言模型】
- [@zPatronus](https://github.com/zijunhz) - 项目维护者 【WebUI】
- [@s7a9](https://github.com/s7a9) - 项目维护者 【知识库】
- [@yfluo](https://github.com/yfluo914) - 项目维护者 【知识库、语言模型】
