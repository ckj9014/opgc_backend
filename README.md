<div align=center>
	<img src="https://user-images.githubusercontent.com/24591259/155003517-152d4bac-a726-48a4-8411-696861dffc81.png">
</div>


# 🤖 Contents
`Over Programmed Good Coding` 백엔드 레포지토리 입니다!<br>
깃헙 정보를 바탕으로 다양한 랭킹정보를 업데이트 합니다.<br>


### 🤩 README.md 에 OPGC 태그 달기
<a href="https://opgc.me/#/users/JAY-Chan9yu" target="_blank"><img src="https://api.opgc.me/githubs/users/JAY-Chan9yu/tag/?theme=basic" /></a>
<a href="https://opgc.me/#/users/JAY-Chan9yu" target="_blank"><img src="https://api.opgc.me/githubs/users/JAY-Chan9yu/tag/?theme=rainbow" /></a>
<a href="https://opgc.me/#/users/JAY-Chan9yu" target="_blank"><img src="https://api.opgc.me/githubs/users/JAY-Chan9yu/tag/?theme=prism" /></a>
<a href="https://opgc.me/#/users/JAY-Chan9yu" target="_blank"><img src="https://api.opgc.me/githubs/users/JAY-Chan9yu/tag/?theme=dracula" /></a>

[OPGC](https://opgc.me/#/main)에 접속해서 깃헙 아이디를 검색하세요! OPGC서버에 등록된 이후에 위 태그를 사용할 수 있습니다. <br><br>
![스크린샷 2022-02-22 오전 2 39 57](https://user-images.githubusercontent.com/24591259/155004723-5ef6be0a-5a7c-4349-a7d8-5e516e7a4b22.png)
<br><br>태그는 사이트에서 리드미 복사하기 버튼을 클릭하면 클립보드에 복사됩니다.<br>
혹은 아래와 같은 형태로 바로 사용 가능합니다 (단, OPGC에 등록된 깃헙아이디만 가능합니다.) <br>
`<img src="https://api.opgc.me/githubs/users/{{깃헙아이디}}/tag/?theme=basic" />` <br>

|옵션명|설명|
|----|----|
|theme|테마 설정 (basic, rainbow, prism, dracula)|


# 🚀 Project
### 💡 Version
```
Python 3.7.9
Django 2.2.17
```
### ☁️  Install
```
pip install -r reqirements/base.txt
```

## 🛠 Architecture
```
├── adapter (외부 api 통신 모듈)
├── api
|   ├── views.py
|   ├── serializers.py
|   └── urls.py
├── apps
|   ├── apps.py 
|   ├── models.py
|   └── admin.py
├── conf
|   ├── settings
|   |   ├── base.py 
|   |   └── prod.py
|   └── urls
├── core (프로젝트 전반적으로 사용되는 코어 로직)
├── scripts
├── static
├── utils
├── templates
├── test_helper(테스트 케이스에서 사용되는 helper 함수들)
├── test (테스트 케이스)
└── requiremetns
```
