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
            # --- 登录步骤 ---
            login_success = False
            if remember_web_cookie:
                print("尝试使用 Cookie 登录...")
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
                # 先访问登录页确认 Cookie 是否有效
                page.goto("https://hub.weirdhost.xyz/auth/login", wait_until="domcontentloaded")
                if "login" in page.url or "auth" in page.url:
                    print("Cookie 登录失效")
                    page.context.clear_cookies()
                else:
                    print("Cookie 登录成功")
                    login_success = True

            if not login_success:
                if not (pterodactyl_email and pterodactyl_password):
                    print("缺少邮箱或密码，无法登录")
                    browser.close()
                    return False
                print("使用邮箱密码登录...")
                page.goto("https://hub.weirdhost.xyz/auth/login", wait_until="domcontentloaded")
                try:
                    # 勾选登录协议
                    page.locator('input.LoginContainer___StyledInput-sc-qtrnpk-4').check()
                except PlaywrightTimeoutError:
                    print("未找到登录协议勾选框")
                page.fill('input[name="username"]', pterodactyl_email)
                page.fill('input[name="password"]', pterodactyl_password)
                page.click('button:has-text("로그인")')

                # 等待登录完成：判断服务器页面按钮是否可见
                time.sleep(3)  # 短暂等待登录跳转
                login_success = True  # 直接标记成功，后面访问服务器页检查按钮

            if not login_success:
                print("登录失败")
                browser.close()
                return False

            # --- 登录成功后访问服务器页面 ---
            print(f"访问服务器页面: {server_url}")
            page.goto(server_url, wait_until="domcontentloaded")

            # 点击续期按钮
            add_button_selector = 'button:has-text("시간 추가")'
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
            print(f"未知错误: {e}")
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
