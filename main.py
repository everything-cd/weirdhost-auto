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
            # 方案一：用 Cookie 登录
            if remember_web_cookie:
                session_cookie = {
                    'name': 'remember_web_59ba36addc2b2f9401580f014c7f58ea4e30989d',
                    'value': remember_web_cookie,
                    'domain': 'hub.weirdhost.xyz',
                    'path': '/',
                    'expires': int(time.time()) + 3600 * 24 * 365,
                    'httpOnly': True,
                    'secure': True,
                    'sameSite': 'Lax'
                }
                page.context.add_cookies([session_cookie])
                page.goto(server_url, wait_until="domcontentloaded")
                if "login" in page.url or "auth" in page.url:
                    page.context.clear_cookies()
                    remember_web_cookie = None

            # 方案二：用邮箱密码登录
            if not remember_web_cookie:
                login_url = "https://hub.weirdhost.xyz/auth/login"
                page.goto(login_url, wait_until="domcontentloaded")

                # 勾选登录协议
                checkbox_selector = 'input.LoginContainer___StyledInput-sc-qtrnpk-4'
                page.wait_for_selector(checkbox_selector)
                page.check(checkbox_selector)

                # 填写邮箱和密码
                email_selector = 'input[name="username"]'
                password_selector = 'input[name="password"]'
                login_button_selector = 'button:has-text("로그인")'

                page.wait_for_selector(email_selector)
                page.fill(email_selector, pterodactyl_email)
                page.fill(password_selector, pterodactyl_password)

                page.wait_for_selector(login_button_selector)
                with page.expect_navigation(wait_until="domcontentloaded", timeout=60000):
                    page.click(login_button_selector)

                if "login" in page.url or "auth" in page.url:
                    print("邮箱密码登录失败")
                    page.screenshot(path="login_fail_error.png")
                    browser.close()
                    return False

            # 确保在服务器页面
            if page.url != server_url:
                page.goto(server_url, wait_until="domcontentloaded")
                if "login" in page.url:
                    page.screenshot(path="server_page_nav_fail.png")
                    browser.close()
                    return False

            # 点击“시간 추가”按钮
            add_button_selector = 'button:has-text("시간 추가")'
            add_button = page.locator(add_button_selector)
            add_button.wait_for(state='visible', timeout=30000)
            add_button.click()
            time.sleep(5)

            browser.close()
            print("任务完成")
            return True

        except PlaywrightTimeoutError as e:
            print(f"超时错误: {e}")
            page.screenshot(path="timeout_error.png")
            browser.close()
            return False
        except Exception as e:
            print(f"未知错误: {e}")
            page.screenshot(path="general_error.png")
            browser.close()
            return False

if __name__ == "__main__":
    print("开始执行添加服务器时间任务...")
    success = add_server_time()
    exit(0 if success else 1)
