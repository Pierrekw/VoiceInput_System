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


�㵱ǰ�ĳ����ǵ��͵� Git **��ʱ�л���֧����**���̡���������������ȫ���Ƽ��Ĳ������裬�������㵱ǰ�� `feature/integrated-voice-recognition` ��֧����δ�ύ�޸ġ������л��Ϸ�֧������ `main` �� `feature/excel-enhancements`�����������������

---

## ? ���� 1�����浱ǰ������δ�ύ�ĸ��ģ�

### ��� A������**δ�ݴ�/δ�ύ�Ĵ����޸�**
ʹ�� `git stash` ��ʱ���棨�ȫ����
```bash
git stash push -m "WIP: integrated voice recognition"
```
> ���ѹ��������ݴ����ĸĶ�ȫ����������������������ɾ��������л���֧��

### ��� B�����Ѿ� `git add` ����û `commit`
ͬ������ `git stash`�����ᱣ�����ݴ��δ�ݴ�ĸ��ġ�

> ?? `git stash` ��**���ز���**����Ӱ��Զ�̣�Ҳ�������ԱȨ�ޡ�

---

## ? ���� 2���л����Ϸ�֧

��ȷ���������µ�Զ����Ϣ��
```bash
git fetch origin
```

Ȼ���л���Ŀ���Ϸ�֧������ `main`����
```bash
git switch main
```

���л����������ܷ�֧���� `feature/excel-enhancements`����
```bash
git switch feature/excel-enhancements
```

> �������û�и÷�֧����Զ���У�Git ���Զ����������١�

---

## ? ���� 3�����Ϸ�֧���޸� & �ύ

�����ڿ��������޸ġ����ԡ��ύ��
```bash
# �޸��ļ�...
git add .
git commit -m "�޸���ʷ��¼��ʾ����"
```

---

## ? ���� 4���л�ԭ��֧���ָ�����

```bash
git switch feature/integrated-voice-recognition
git stash pop   # �ָ�֮ǰ����Ĺ���
```

---

## ?? ���������ͻ�������족����ô�죿

����ִ�� `git stash pop` ʱ��**����Ϸ�֧���޸ĺ��� stash �������޸���ͬһ���ļ���ͬһ����**��Git �ᱨ��ͻ�����磺

```
Auto-merging src/app.py
CONFLICT (content): Merge conflict in src/app.py
```

### ?? ��ͻ��������

1. **�򿪳�ͻ�ļ�**����ῴ�����ƣ�
   ```python
   <<<<<<< Updated upstream
   print("old code from main")
   =======
   print("new code from stash")
   >>>>>>> Stashed changes
   ```

2. **�ֶ��༭**����������Ҫ�Ĵ��룬ɾ�� `<<<<<<<`, `=======`, `>>>>>>>` ��ǡ�

3. **��ǳ�ͻ�ѽ��**��
   ```bash
   git add src/app.py
   ```

4. **��ɻָ�**��stash ���Զ�ɾ������
   ```bash
   git stash drop   # ��� pop ��û�Զ�ɾ���ֶ�ɾ��
   ```

> ?? ��ͻ����������˵��������֧������ͬһ��������Ϊ�����ߣ�������ñ����Ĳ����߼���

---

## ? ���⽨�飺�鿴 stash ���ݣ������������

- �鿴 stash �б�
  ```bash
  git stash list
  ```
- �鿴 stash �������ʲô��
  ```bash
  git stash show -p
  ```

---

## ?? ���������ܽ�

```bash
# 1. ���浱ǰ����
git stash push -m "WIP voice"

# 2. �е��Ϸ�֧
git switch main

# 3. �޸Ĳ��ύ
# ... �༭ ...
git add .
git commit -m "fix bug in main"

# 4. �л�ԭ��֧
git switch feature/integrated-voice-recognition

# 5. �ָ�����������������ͻ��
git stash pop
```

---

���������Ҿ���Ҫ�л��ĸ����Ϸ�֧�������� `main` ���� `feature/excel-enhancements`�����ҿ��Ը��㶨�������Ҫ��



�㵣�� **`feature/integrated-voice-recognition`** �� **`feature/excel-enhancements`** ������֧�޸��ļ��ࡢ�ϲ���ͻ���ӣ����Ƿǳ�����Ĺ��ǡ��� Git �ṩ�˶��ֲ�����**��ȫ���ɿص���ɺϲ�**��������һ��**�Ƽ�����**�������̶Ƚ��ͷ��գ�

---

## ? ��һ����ȷ���������ɾ���������ţ�
```bash
# �鿴��ǰ״̬
git status

# �����δ�ύ���޸ģ��� stash
git stash push -m "WIP before merge"
```

---

## ? �ڶ�����ͬ������Զ�̷�֧
```bash
git fetch origin
```

---

## ? �������������ϲ������Ƽ����ԣ�

### ?? **�Ƽ����������·�֧�����ϲ����ȫ��**
��Ҫֱ������һ���ܷ�֧�� merge�����Ǵ���һ��**��ʱ�ϲ���֧**��

```bash
# ��������һ����֧������ excel-enhancements�������ϲ���֧
git switch -c merge-voice-and-excel origin/feature/excel-enhancements
```

> ������ʹ�ϲ�ʧ�ܻ��ͻ���أ�Ҳ������Ⱦԭ�з�֧��

---

## ? ���Ĳ���Ԥ�����죨�ؼ�����

### 1. �鿴������֧�޸�����Щ�ļ���
```bash
git diff --name-only origin/feature/excel-enhancements origin/feature/integrated-voice-recognition
```

### 2. �鿴������죨��ѡ����
```bash
git diff origin/feature/excel-enhancements..origin/feature/integrated-voice-recognition
```

> ?? ������ִ����ص��ļ������綼���� `main.py`, `config.yaml`, `text_processor.py`������Ҫ�ص�׼�������ͻ��

---

## ? ���岽��ִ�кϲ�������ʱ��֧�ϣ�

```bash
git merge origin/feature/integrated-voice-recognition
```

### ���ܽ����
- **�Զ��ϲ��ɹ�** �� ��ϲ�����Թ��ܺ�ɺϲ������ɡ�
- **���ֳ�ͻ** �� ������һ����

---

## ? �������������ͻ���������ɣ�

### 1. �鿴��ͻ�ļ���
```bash
git status
```

### 2. ����򿪳�ͻ�ļ�����ῴ����
```python
<<<<<<< HEAD
# excel-enhancements �Ĵ���
=======
# integrated-voice-recognition �Ĵ���
>>>>>>> origin/feature/integrated-voice-recognition
```

### 3. **�ֶ��༭**����������Ҫ���߼���ɾ������С�

### 4. ��ǳ�ͻ�ѽ����
```bash
git add <resolved-file.py>
```

### 5. ��ɺϲ���
```bash
git commit  # Git ���Զ����ɺϲ��ύ��Ϣ
```

> ?? **����**�����ĳ���ļ�����ȫ����ĳһ��֧�İ汾�������ã�
> ```bash
> # ��ȫ���� voice ��֧�� version
> git checkout --theirs path/to/file.py
> git add path/to/file.py
>
> # ����ȫ���� excel ��֧�� version
> git checkout --ours path/to/file.py
> git add path/to/file.py
> ```

---

## ? ���߲������Ժϲ�����
- ���г���ȷ�� **����ʶ�� + Excel ���ܶ�����**
- �ر�����������ܽ����Ĳ��֣������������д�� Excel��

---

## ? �ڰ˲�����������������ѡ��

### ?? ѡ�� A���ϲ������ɣ��Ƽ���
```bash
git switch main
git merge merge-voice-and-excel
```

### ?? ѡ�� B������Ϊ���ڼ��ɷ�֧
```bash
git push origin merge-voice-and-excel
```

### ?? ѡ�� C�������ϲ������̫���ң�
```bash
git switch main
git branch -D merge-voice-and-excel  # ɾ����ʱ��֧
git stash pop  # �ָ���֮ǰ�Ĺ���
```

---

## ?? ���⽨�飺����δ���ϲ��Ѷ�

1. **С������**�����ܷ�֧��Ҫ���ڲ��ϲ������� rebase main��
2. **ģ�黯���**���������� Excel ���ܽ������ͨ���ӿ�ͨ�ţ�����ֱ���޸ı˴��ļ�����
3. **ʹ�� `.gitattributes`** ���⻻�з�/�����ͻ��
   ```gitattributes
   *.py text eol=lf
   *.yaml text eol=lf
   ```

---

�����Ը�⣬�ҿ��ԣ�
- ���������������֧**��������Щ�ļ��ص�**
- ����һ��**�Զ��ϲ��ű�**
- ��ָ������ **VS Code / PyCharm �Ŀ��ӻ��ϲ�����** �����ͻ

��Ҫ��

�ǵģ�**Git ��ȫ���ԶԱ�������ͬ·���µ�ͬ���ļ�**����ʹ���ǲ���ͬһ��Ŀ¼������һ������Ŀ��Ŀ¼��һ���� `New20251027/` ��Ŀ¼����

�����ʹ����������ֱ�ӱȽ��������ļ������ݲ��죺

```bash
git diff --no-index main_f.py New20251027/main_f.py
```

### ˵����
- `--no-index`������ Git **��Ҫֻ�ԱȰ汾���е��ļ�**����������Ա����������ļ�����ʹ����һ���������������ݴ���/�ύ��ʷ�У���
- ������������ڣ�
  - �����������ļ�
  - һ���Ѹ����ļ� + һ��δ�����ļ�
  - ����δ�����ļ�

---

### �������ñ��壺

#### 1. **�Աȵ�ǰ�������������ļ����Ƽ����������**
```bash
git diff --no-index main_f.py New20251027/main_f.py
```

#### 2. **�Ա�ĳ���ύ�е��ļ� vs �������ļ�**
```bash
git diff HEAD:main_f.py New20251027/main_f.py
```

#### 3. **������ļ���������飩**
```bash
git diff --no-index main_f.py New20251027/main_f.py > diff_main_f.txt
```

---

### ?? С���ɣ�����㾭��Ҫ�Ա������ļ�������д�� alias
�� Git Bash �����У�
```bash
git config --global alias.dcmp 'diff --no-index'
```
֮��Ϳ��Լ�дΪ��
```bash
git dcmp main_f.py New20251027/main_f.py
```

---

### ע�����
- ��� `New20251027/main_f.py` ��**δ�� Git ���ٵ��ļ�**���� `git status` ��ʾΪ untracked����`--no-index` ��Ȼ��������������
- ��������� VS Code��PyCharm �� IDE �п��ӻ��Աȣ�Ҳ����ֱ�Ӵ������ļ���ʹ�á�Compare Selected�����ܡ�

---

��Ҫ�Ұ�������һ���ű����Զ��Ա� `New20251027/` �������ļ����Ŀ¼ͬ���ļ��Ĳ�����

̫���ˣ������ڴ���һ��**�ɾ����ȶ���״̬**��

- ? ��ǰ��֧��`merge-voice-and-excel`
- ? �ѳɹ��ϲ� `feature/integrated-voice-recognition` �� `feature/excel-enhancements`
- ? �������ɾ�����δ�ύ���ģ�
- ? ������ 16 �����ύ�������ϲ��ύ��֮ǰ�Ĺ����ύ��

---

### ?? ����������������¼����£�

#### 1. **���Թ����Ƿ�����**
```bash
python main_f.py
```
ȷ����
- ����ʶ�𣨺� energy VAD / TEN VAD������
- Excel ����/ģ�幦������
- GUI �����ޱ���

> ?? �ر�ע�⣺��֮ǰ������ ��debug ģ�� lib ���� Ӧ������ `feature/voice-command-fix-with-history` ��֧�޸����������޸��Ѱ����ںϲ��У�����Ӧ�ѽ����

---

#### 2. **����ѡ�����ͺϲ���֧��Զ�̣����ڱ��ݻ�Э����**
```bash
git push origin merge-voice-and-excel
```
������ĺϲ��ɹ�������Զ�̱��ݣ�Ҳ�����Ŷ� review��

---

#### 3. **�����Ƿ�ϲ������ɣ��� `main`��**
�����ȷ�Ϲ����ȶ������Ժϲ��� `main`��

```bash
git switch main
git pull origin main          # ȷ�� main ����
git merge merge-voice-and-excel
git push origin main
```

> ?? ��� `main` ���������ύ�������� `git pull` �� merge�������ͻ��

---

#### 4. **����ѡ��ɾ����ʱ��֧������/Զ�̣�**
�ϲ���ɺ����������Ҫ `merge-voice-and-excel`��
```bash
# ɾ�����ط�֧
git branch -d merge-voice-and-excel

# ��������͵�Զ�̣�Ҳɾ��Զ�̷�֧
git push origin --delete merge-voice-and-excel
```

---

### ?? �ܽ�
�����ڴ���**����״̬**����ͻ�ѽ���������Ѻϲ����������ɾ�����һ������**���� + �����Ƿ񼯳ɵ�����**��

��Ҫ�Ұ���дһ�������� checklist���򡰻㱨�õĹ�����ʾ�ű�����

ͬ��Git

git checkout -B develop origin/develop   # ȷ������ develop ��Զ��һ��
git pull origin develop                  # �ٴ���ȡ����Ȼͨ�������£�
# ���֮ǰ stash ���������ã�
git stash pop