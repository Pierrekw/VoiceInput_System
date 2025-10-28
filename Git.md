������� `git log` ��������� `--date` �� `--pretty` ��������ʾ�ύʱ�䡣�������Ƽ������**�ڱ��� `--all --oneline --graph --decorate` �Ļ���������ʱ����ʾ**��

```bash
git log --all --graph --decorate --pretty=format:"%h %ad %d %s" --date=short
```

### ������˵����
- `%h`����̵� commit hash���� `a1b2c3d`��
- `%ad`���������ڣ�author date������ʽ�� `--date=` ����
- `%d`��������Ϣ�����֧����tag���� `decorate` ���ݣ�
- `%s`���ύ��Ϣ��subject��
- `--date=short`�����ڸ�ʽΪ `YYYY-MM-DD`����Ҳ������ `iso`��`relative` �ȣ�

---

### ��������ʱ���ʽѡ�
| ѡ�� | ʾ�� |
|------|------|
| `--date=short` | `2025-10-28` |
| `--date=iso` | `2025-10-28 14:30:00 +0800` |
| `--date=relative` | `2 hours ago` |
| `--date=local` | ʹ�ñ���ʱ�� |

---

### �������ϣ����һ����ʾ������ʱ�䣬����������
```bash
git log --all --graph --decorate --oneline --date=short --pretty=format:"%h %ad %d %s"
```

> ?? ע�⣺`--oneline` ʵ������ `--pretty=oneline` �ļ�д���Ḳ���Զ��� `--pretty=format:...`������**����ͬʱ�� `--oneline` �� `--pretty=format`**�����������б����� `--oneline` ����ʾ�⣬ʵ��Ӧ**ȥ�� `--oneline`**������ʱ�䲻����ʾ��

---

### ? �����Ƽ������ʱ�䡢ͼ�Ρ����з�֧����ࣩ��
```bash
git log --all --graph --decorate --pretty=format:"%C(auto)%h %C(green)%ad %C(reset)%d %s" --date=short
```

����汾��������ɫ��`%C(auto)` �Զ���ɫ�����Ӿ���������

Ҫ�� Git ��**��ʱ���浱ǰ�������л�����һ����֧���п��������޸������ٺϲ�����**���Ƽ�ʹ�����±�׼���̣�

---

### ? ����˵��
- ���� `main` ��ĳ�����ܷ�֧�Ϲ�����������**��û���**
- ������Ҫ**��ʱ�е���һ����֧**������ `hotfix` �� `dev`�����޸�
- ��ɺ�Ҫ**���޸ĺϲ���ԭ��֧**

---

## ?? ��ȷ��������

### 1. **���浱ǰδ��ɵĹ�������ѡ��**
�������δ�ύ�ĸ��ģ����ֲ������� commit�������� `stash`��

```bash
git stash push -m "��ʱ���� feature ����"
```

###> ���ѵ�ǰ���������ݴ����ĸĶ���������������������ɾ���***

---

### 2. **�л���Ŀ���֧**
```bash
git checkout target-branch      # ���� git checkout dev
# �������﷨
git switch target-branch
```

> ���Ŀ���֧�����ڣ������ã�
> ```bash
> git switch -c new-hotfix-branch
> ```

---

### 3. **��Ŀ���֧�Ͽ������ύ**
```bash
# �޸��ļ�...
git add .
git commit -m "�޸�ĳ������"
```

---

### 4. **�л���ԭ���ķ�֧**
```bash
git switch original-branch      # ���� git switch main ����Ĺ��ܷ�֧
```

---

### 5. **�ָ�֮ǰ�Ĺ���������� stash��**
```bash
git stash pop   # �ָ����һ�� stash ��ɾ����
# ��
git stash apply # �ָ������� stash�����ڶ�θ��ã�
```

> ����г�ͻ���ֶ�������ɡ�

---

### 6. **�ϲ�Ŀ���֧���޸�**
```bash
git merge target-branch
```

���磺
```bash
git merge hotfix-login-bug
```

> ���� `target-branch` �� commit �ϲ�����ǰ��֧��

---

## ?? ʾ�����̣�������

```bash
# ��ǰ�� feature-a������δ���
git stash push -m "WIP on feature A"

# �е� main �޸����� bug
git switch main
# �޸Ĵ���...
git add .
git commit -m "Fix critical bug in auth"

# �л� feature-a
git switch feature-a

# �ָ�֮ǰ�Ĺ���
git stash pop

# �� main ���޸��ϲ���������ѡ�����Ƽ���
git merge main
```

---

## ?? ���佨��

- �����ֻ����**��ʱ���Ի�鿴������֧**������Ҫ `stash`��ֱ�� `git switch` ���ɣ�ǰ���ǹ������ɾ�����
- ������Ѿ����� commit����**����Ҫ stash**��ֱ���л���֧���ɡ�
- �ϲ�ǰ������ `git pull` ȷ����֧���¡�

---

��Ҫ�Ҹ�����ľ����֧�������� `main`��`dev`��`feature/xxx`�����ɶ���������

�����**ԭ����ĳ����֧���޸ĵ���δ�ύ������ stash�����ļ�**��**Ӧ�õ����л��ķ�֧������ `feature/integrated-voice-recognition`����**������ Git �зǳ������ĳ�������������������ȫ�Ĳ������裺

---

### ? �����ع�
- ����ĳ����֧������ `main` �� detached HEAD���������޸�
- ��ִ���� `git stash` ��������Щ�޸ģ��������־�����Ѿ����ˣ�
- Ȼ���㳢���л���Զ�̷�֧����ʧ���ˣ���Ϊ����ֱ�� `switch` �� `origin/xxx`��
- �������룺**����ȷ�ı��ع��ܷ�֧�ϻָ���Щ�޸�**

---

### ? ��ȷ��������

#### 1. **�������л������ع��ܷ�֧**
```bash
git switch -c feature/integrated-voice-recognition --track origin/feature/integrated-voice-recognition
```
> ������Զ�̷�֧����ͬ�����ط�֧�����Զ����ø��١�

#### 2. **�ָ���֮ǰ stash ���޸�**
```bash
git stash pop
```
> �������һ�� stash �����ݻָ��������������� stash �б���ɾ����

����㲻ȷ�� stash �б����ݣ������Ȳ鿴��
```bash
git stash list
```
������ƣ�
```
stash@{0}: On (no branch): ��ʱ���� feature ����
```

---

### ? ����㻹û stash������δ�ύ�޸ģ�
�����**��û stash**�������������޸ģ�Ҳ����ֱ���л���֧��ǰ���� Git ��Ϊ�����ͻ����
```bash
git switch feature/integrated-voice-recognition
```
Git ���Զ�Я��δ�ύ�ĸ��ĵ��·�֧��ֻҪ�ļ�����ͻ����

> ?? ����� Git �ܾ��л�����ʾ��would be overwritten�������Ǿͱ����� `stash`��

---

### ? ��֤���
- ���� `git status`��ȷ������޸��ѳ������·�֧
- ���� `git branch`��ȷ�ϵ�ǰ�� `feature/integrated-voice-recognition`
- Ȼ������� `git add` + `git commit` �ύ��Щ�޸�

---

### ?? �ܽ�����㵱ǰ�������Ҫ�ģ�
```bash
# 1. �������л������ع��ܷ�֧
git switch -c feature/integrated-voice-recognition --track origin/feature/integrated-voice-recognition

# 2. �ָ�֮ǰ stash ���޸�
git stash pop
```

��ɺ���ԭ���޸ĵ��ļ��͡��Ž������·�֧�����Լ����������ύ��

��Ҫ�Ұ����鵱ǰ״̬������ `git status` �������