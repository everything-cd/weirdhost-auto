import os
import time
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

def add_server_time(server_url="https://hub.weirdhost.xyz/server/027a2f87"):
    """
    登录 hub.weirdhost.xyz 并点击 "시간 추가" 按钮。
    优先使用 REMEMBER_WEB_COOKIE 进行会话登录，如果失效则回退到邮箱密码登录。
    登录成功后会刷新 Cookie 并打印，用于下次 GitHub Actions。
    """
    # 环境变量
    remember_web_cookie = os.environ.get('REMEMBER_WEB_COOKIE')
    pterodactyl_email = os.environ.get('PTERODACTYL_EMAIL')
    pterodactyl_password = os.environ.get('PTERODACTYL_PASSWORD')

    if not (remember_web_cookie or (pterodactyl_email and pterodactyl_password)):
        print("错误: 缺少登录凭据，请设置 REMEMBER_WEB_COOKIE 或 PTERODACTYL_EMAIL/PTERODACTYL_PASSWORD。")
        return False

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.set_default_timeout(90000)  # 90秒超时

        try:
            # --- Cookie 登录 ---
            if remember_web_cookie:
                print("检测到 REMEMBER_WEB_COOKIE，尝试使用 Cookie 登录...")
                cookie_dict = {
                    'name': 'remember_web_59ba36addc2b2f9401580f014c7f58ea4e30989d',
                    'value': remember_web_cookie.strip(),
                    'domain': '.hub.weirdhost.xyz',
                    'expires': int(time.time()) + 3600 * 24 * 365 * 3,  # 3 年
                    'path': '/',
                    'httpOnly': True,
                    'secure': True,
                    'sameSite': 'Lax'
                }
                try:
                    page.context.add_cookies([cookie_dict])
                    page.goto(server_url, wait_until="domcontentloaded", timeout=90000)
                    if "login" in page.url or "auth" in page.url:
                        print("Cookie 登录失败，将回退到邮箱密码登录。")
                        page.context.clear_cookies()
                        remember_web_cookie = None
                    else:
                        print("Cookie 登录成功，已进入服务器页面。")
                except Exception as e:
                    print(f"Cookie 设置或跳转失败: {e}")
                    page.context.clear_cookies()
                    remember_web_cookie = None

            # --- 邮箱密码登录 ---
            if not remember_web_cookie:
                if not (pterodactyl_email and pterodactyl_password):
                    print("错误: Cookie 无效且未提供邮箱/密码。")
                    browser.close()
                    return False

                login_url = "https://hub.weirdhost.xyz/auth/login"
                print(f"访问登录页面: {login_url}")
                page.goto(login_url, wait_until="domcontentloaded", timeout=90000)

                email_selector = 'input[name="username"]'
                password_selector = 'input[name="password"]'
                login_button_selector = 'button[type="submit"]'

                page.wait_for_selector(email_selector)
                page.wait_for_selector(password_selector)
                page.wait_for_selector(login_button_selector)

                page.fill(email_selector, pterodactyl_email)
                page.fill(password_selector, pterodactyl_password)

                print("点击登录按钮...")
                with page.expect_navigation(wait_until="domcontentloaded", timeout=60000):
                    page.click(login_button_selector)

                if "login" in page.url or "auth" in page.url:
                    error_text = page.locator('.alert.alert-danger').inner_text().strip() if page.locator('.alert.alert-danger').count() > 0 else "未知错误"
                    print(f"邮箱密码登录失败: {error_text}")
                    page.screenshot(path="login_fail.png")
                    browser.close()
                    return False
                else:
                    print("邮箱密码登录成功！")

                # --- 刷新 Cookie ---
                cookies = page.context.cookies()
                for c in cookies:
                    if c['name'].startswith('remember_web_'):
                        print(f"刷新后的 REMEMBER_WEB_COOKIE: {c['value']}")

            # --- 确认在服务器页面 ---
            if page.url != server_url:
                page.goto(server_url, wait_until="domcontentloaded", timeout=90000)
                if "login" in page.url:
                    print("导航失败，会话可能失效。")
                    page.screenshot(path="server_nav_fail.png")
                    browser.close()
                    return False

            # --- 点击 "시간 추가" 按钮 ---
            add_button_selector = 'button:has-text("시간 추가")'
            print(f"查找按钮 '{add_button_selector}' ...")
            add_button = page.locator(add_button_selector)
            add_button.wait_for(state='visible', timeout=30000)
            add_button.click()
            print("成功点击 '시간 추가' 按钮！")
            time.sleep(5)

            browser.close()
            print("任务完成。")
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
    if success:
        print("任务执行成功。")
        exit(0)
    else:
        print("任务执行失败。")
        exit(1)
