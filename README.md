# Syntax Parser

**《编译原理》课程设计，基于 LR (1) 分析的类 C 语言语法分析器**

*<u>本项目配套的 [词法分析器](https://github.com/LIU42/LexicalParser)</u>*

## 项目简介

本项目为基于 LR (1) 分析的类 C 语言语法分析器，可以实现针对一种类似 C 语言程序的 Token 序列（由 [词法分析器](https://github.com/LIU42/LexicalParser) 生成）进行语法分析，给出合法判断、出错位置及大致原因。

本项目提供的默认文法支持除了：

- 复杂的指针类型（如函数指针，行指针等）

- 关键字 typedef 及相关的类型定义

- 编译预处理指令

以外大部分的 C 语言语法规则。此外还有一些额外的关键字，详见 [词法分析器](https://github.com/LIU42/LexicalParser) 中的介绍。

## 实现方案

### 工作流程

整个项目的工作流程如下：

1. 首先读入文法配置文件（<u>grammars/grammar.json</u>）中描述语法规则的带有拓广产生式的 2 型文法，并根据该文法利用项目集规范族法构造识别活前缀的有穷自动机（状态转换表）。

2. 其次根据状态转换表，判断项目类型，逐一添加 ACTION 表项和 GOTO 表项，分别构造 ACTION 表和 GOTO 表。

3. 最后根据 ACTION 表和 GOTO 表，以及错误信息配置文件（<u>grammars/message.json</u>）利用 LR (1) 分析流程，对输入的 Token 序列进行语法分析和错误处理。

当检测到语法错误时，采用恐慌模式（Panic）错误恢复策略，即不断丢弃下一个 Token，直到找到一个能够进行正常分析的 Token 继续分析。

### 伪代码描述

```
创建状态栈和符号栈;

while (指针未到达末尾 && 分析结束标志为假) {
    根据指针位置取出待分析的 Token;
    查询 ACTION 表获取该 Token 对应的操作;

    if (无对应操作) {
        ACTION 出错处理程序;
    } else if (为接受操作) {
        分析结束标志设为真;
    } else if (为移进操作) {
        当前 Token 压入符号栈;
        对应 ACTION 表值压入状态栈;
        指针后移一位;
    } else if (为归约操作) {
        从符号栈中弹出指定数量的符号进行归约，将归约后的符号重新压入栈中;
        从状态栈中弹出相同数量的符号，之后用栈顶状态和归约后的符号查询 GOTO 表;

        if (GOTO 表查询结果为空) {
            GOTO 出错处理程序;
        }
        GOTO 表查询结果压入状态栈中;
    }
}
```

## 使用说明

grammars 目录下的 grammar.json 文件为本项目的文法配置文件，本项目提供一种默认的文法，也可根据需要调整其中内容，其结构如下：

```json5
{
    "formulas": [
        /*
         * 语法规则文法产生式列表，要求 II 型文法
         * 编写规则形如："[SelectionStatement] -> <keywords,if> <bounds,(> [Expression] <bounds,)> [Statement]"
         * 非终结符以[]包裹，名称可自定义
         * 终结符按照 Token 的表示规则：<所属类型,内容>
         * 不同的符号间以空格分隔
         */
    ]
}
```

grammars 目录下的 message.json 文件为本项目的错误信息配置文件，用于根据出错的符号确定错误原因，本项目提供一组默认的配置，也可根据需要调整其中内容，其结构如下：

```json5
{
    "messages": [
        {
            "token": /* 出错的 Token，表示规则为 <所属类型,内容> */,
            "message": /* 对应的出错原因描述 */
        }
        // 类似地可添加多个规则
    ],
    "defaults": // 默认的出错原因描述，在没有成功匹配时调用
}
```

本项目不依赖任何第三方库，由于文法产生式数量较多，构建 ACTION 表和 GOTO 表为一项耗时操作。运行 tables.py 文件即可根据配置的文法生成 ACTION 表和 GOTO 表并保存在本地：

- 生成的 ACTION 表和 GOTO 表位于 tables 目录下，其中 action.txt 文件为 ACTION 表内容，goto.txt 文件为 GOTO 表内容。

- 生成报告位于 reports 目录下，其中 items.txt 文件为生成的项目集，conflicts.txt 文件为表项冲突。

运行主程序 main.py 即可进行语法分析。本项目提供了一些测试用例，也可根据需要调整输入和输出文件路径。
