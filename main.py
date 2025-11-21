import os
import time
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

def add_server_time(server_url="https://hub.weirdhost.xyz/server/027a2f87"):
    remember_web_cookie = os.environ.get('REMEMBER_WEB_COOKIE')
    pterodactyl_email = os.environ.get('PTERODACTYL_EMAIL')
    pterodactyl_password = os.environ.get('PTERODACTYL_PASSWORD')

    if not (remember_web_cookie or (pterodactyl_email and pterodactyl_password)):
        print("缺少登录凭据")
        return False

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.set_default_timeout(90000)

        try:
            # --- Cookie 登录 ---
            if remember_web_cookie:
                print("尝试使用 Cookie 登录...")
                page.context.add_cookies([{
                    'name': 'remember_web_59ba36addc2b2f9401580f014c7f58ea4e30989d',
                    'value': remember_web_cookie,
                    'domain': 'hub.weirdhost.xyz',
                    'path': '/',
                    'expires': int(time.time()) + 3600*24*365,
                    'httpOnly': True,
                    'secure': True,
                    'sameSite': 'Lax'
                }])
                page.goto(server_url, wait_until="domcontentloaded")
                if "login" in page.url or "auth" in page.url:
                    print("Cookie 登录失败，将回退到邮箱密码登录")
                    page.context.clear_cookies()
                    remember_web_cookie = None
                else:
                    print("Cookie 登录成功！")

            # --- 邮箱密码登录 ---
            if not remember_web_cookie:
                print("使用邮箱密码登录...")
                login_url = "https://hub.weirdhost.xyz/auth/login"
                page.goto(login_url, wait_until="domcontentloaded")

                # 勾选登录协议
                try:
                    page.check('input[type="checkbox"]')
                except PlaywrightTimeoutError:
                    pass

                # 填写账号密码
                page.fill('input[name="username"]', pterodactyl_email)
                page.fill('input[name="password"]', pterodactyl_password)

                # 点击登录按钮
                page.click('button:has-text("로그인")')

                # 等待登录按钮消失或超时
                try:
                    page.wait_for_selector('button:has-text("로그인")', state='detached', timeout=30000)
                    print("邮箱密码登录成功！")
                except PlaywrightTimeoutError:
                    print("邮箱密码登录失败！登录按钮仍在页面")
                    page.screenshot(path="login_fail_error.png")
                    browser.close()
                    return False

            # --- 打开服务器页面 ---
            page.goto(server_url, wait_until="domcontentloaded")
            print(f"访问服务器页面: {server_url}")

            # --- 点击 '시간 추가' 按钮 ---
            add_button_selector = 'span:has-text("시간 추가")'
            try:
                add_button = page.locator(add_button_selector)
                add_button.wait_for(state='visible', timeout=30000)
                add_button.click()
                print("成功点击 '시간 추가' 按钮")
                time.sleep(5)
                browser.close()
                return True
            except PlaywrightTimeoutError:
                print("未找到或不可点击 '시간 추가' 按钮")
                page.screenshot(path="add_6h_button_not_found.png")
                browser.close()
                return False

        except Exception as e:
            print(f"执行过程中发生错误: {e}")
            page.screenshot(path="general_error.png")
            browser.close()
            return False

if __name__ == "__main__":
    print("开始执行添加服务器时间任务...")
    success = add_server_time()
    if success:
        print("任务执行成功")
        exit(0)
    else:
        print("任务执行失败")
        exit(1)
