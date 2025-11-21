import os
import time
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

def add_server_time(server_url="https://hub.weirdhost.xyz/server/027a2f87"):
    """
    登录 hub.weirdhost.xyz 并点击 "시간 추가" 按钮进行续期。
    优先使用 REMEMBER_WEB_COOKIE，如果没有则使用邮箱密码登录。
    """
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
            # --- 优先 Cookie 登录 ---
            if remember_web_cookie:
                print("尝试使用 Cookie 登录...")
                session_cookie = {
                    'name': 'remember_web_59ba36addc2b2f9401580f014c7f58ea4e30989d',
                    'value': remember_web_cookie,
                    'domain': 'hub.weirdhost.xyz',
                    'path': '/',
                    'expires': int(time.time()) + 3600*24*365,
                    'httpOnly': True,
                    'secure': True,
                    'sameSite': 'Lax'
                }
                page.context.add_cookies([session_cookie])
                page.goto(server_url, wait_until="domcontentloaded")
                
                if "login" in page.url or "auth" in page.url:
                    print("Cookie 登录失败，将尝试邮箱密码登录")
                    page.context.clear_cookies()
                    remember_web_cookie = None
                else:
                    print("Cookie 登录成功！")

            # --- 邮箱密码登录 ---
            if not remember_web_cookie:
                if not (pterodactyl_email and pterodactyl_password):
                    print("没有可用的邮箱密码登录信息，无法登录")
                    browser.close()
                    return False

                login_url = "https://hub.weirdhost.xyz/auth/login"
                print("使用邮箱密码登录...")
                page.goto(login_url, wait_until="domcontentloaded")

                # 等待登录表单
                email_selector = 'input[name="username"]'
                password_selector = 'input[name="password"]'
                login_button_selector = 'button:has-text("로그인")'
                agreement_checkbox_selector = 'input[type="checkbox"]'

                page.wait_for_selector(email_selector)
                page.wait_for_selector(password_selector)
                page.wait_for_selector(login_button_selector)

                # 填写账号密码
                page.fill(email_selector, pterodactyl_email)
                page.fill(password_selector, pterodactyl_password)

                # 勾选协议
                if page.locator(agreement_checkbox_selector).count() > 0:
                    page.check(agreement_checkbox_selector)

                # 点击登录按钮并等待导航
                with page.expect_navigation(wait_until="domcontentloaded", timeout=60000):
                    page.click(login_button_selector)

                # 检查登录是否成功
                if "login" in page.url or "auth" in page.url:
                    print("邮箱密码登录失败！")
                    page.screenshot(path="login_fail_error.png")
                    browser.close()
                    return False
                else:
                    print("邮箱密码登录成功！")

            # --- 访问服务器页面 ---
            print(f"访问服务器页面: {server_url}")
            page.goto(server_url, wait_until="domcontentloaded")
            page.wait_for_timeout(2000)  # 等待 2 秒，确保按钮渲染完成

            # --- 点击 시간 추가 按钮 ---
            add_button_selector = 'span:has-text("시간 추가")'
            try:
                add_button = page.locator(add_button_selector)
                add_button.wait_for(state='visible', timeout=30000)
                add_button.click()
                print("成功点击 '시간 추가' 按钮")
                time.sleep(5)
                print("续期任务完成！")
                browser.close()
                return True
            except PlaywrightTimeoutError:
                print("未找到或不可点击 '시간 추가' 按钮")
                page.screenshot(path="add_button_not_found.png")
                browser.close()
                return False

        except Exception as e:
            print(f"执行过程中发生未知错误: {e}")
            page.screenshot(path="general_error.png")
            browser.close()
            return False

if __name__ == "__main__":
    print("开始执行添加服务器时间任务...")
    success = add_server_time()
    if success:
        print("任务执行成功！")
        exit(0)
    else:
        print("任务执行失败！")
        exit(1)
