import os
import re

def resolve_file(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Regex to find conflict blocks
        # This handles simple conflicts. Nested conflicts might break it.
        # Pattern: <<<<<<< HEAD ... ======= ... >>>>>>> ...
        pattern = re.compile(r'<<<<<<< HEAD\n(.*?)\n=======\n(.*?)\n>>>>>>> .*?\n', re.DOTALL)
        
        if not pattern.search(content):
            print(f"No conflict markers found in {filepath}")
            return

        new_content = pattern.sub(r'\1\n', content)
        
        # Check if there are still markers (nested or malformed)
        if '<<<<<<<' in new_content:
            print(f"⚠️ Warning: Remaining conflict markers in {filepath}")
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print(f"✅ Resolved {filepath}")

    except Exception as e:
        print(f"❌ Error resolving {filepath}: {e}")

if __name__ == "__main__":
    # List of files to resolve (from grep output)
    files = [
        r"c:\Users\leerg\OneDrive\Desktop\sales-os\backend\tests\__init__.py",
        r"c:\Users\leerg\OneDrive\Desktop\sales-os\backend\pytest.ini",
        r"c:\Users\leerg\OneDrive\Desktop\sales-os\backend\main.py",
        r"c:\Users\leerg\OneDrive\Desktop\sales-os\backend\app\services\transcript\__init__.py",
        r"c:\Users\leerg\OneDrive\Desktop\sales-os\backend\app\services\rendering\__init__.py",
        r"c:\Users\leerg\OneDrive\Desktop\sales-os\backend\app\services\enrichment\__init__.py",
        r"c:\Users\leerg\OneDrive\Desktop\sales-os\backend\app\services\coaching\__init__.py",
        r"c:\Users\leerg\OneDrive\Desktop\sales-os\backend\app\schemas\__init__.py",
        r"c:\Users\leerg\OneDrive\Desktop\sales-os\backend\app\models\prospect.py",
        r"c:\Users\leerg\OneDrive\Desktop\sales-os\backend\app\schemas\user.py",
        r"c:\Users\leerg\OneDrive\Desktop\sales-os\backend\app\models\hubspot.py",
        r"c:\Users\leerg\OneDrive\Desktop\sales-os\backend\app\models\content.py",
        r"c:\Users\leerg\OneDrive\Desktop\sales-os\backend\app\models\coaching.py",
        r"c:\Users\leerg\OneDrive\Desktop\sales-os\backend\app\models\base.py",
        r"c:\Users\leerg\OneDrive\Desktop\sales-os\backend\app\middleware\__init__.py",
        r"c:\Users\leerg\OneDrive\Desktop\sales-os\backend\app\integrations\__init__.py",
        r"c:\Users\leerg\OneDrive\Desktop\sales-os\backend\app\integrations\hubspot\__init__.py",
        r"c:\Users\leerg\OneDrive\Desktop\sales-os\backend\app\integrations\hubspot\client.py",
        r"c:\Users\leerg\OneDrive\Desktop\sales-os\backend\app\middleware\rate_limit.py",
        r"c:\Users\leerg\OneDrive\Desktop\sales-os\backend\app\integrations\avoma\__init__.py",
        r"c:\Users\leerg\OneDrive\Desktop\sales-os\backend\app\db\__init__.py",
        r"c:\Users\leerg\OneDrive\Desktop\sales-os\backend\app\core\security.py",
        r"c:\Users\leerg\OneDrive\Desktop\sales-os\backend\app\api\health.py",
        r"c:\Users\leerg\OneDrive\Desktop\sales-os\backend\app\api\webhooks.py",
        r"c:\Users\leerg\OneDrive\Desktop\sales-os\backend\app\api\__init__.py",
        r"c:\Users\leerg\OneDrive\Desktop\sales-os\backend\app\core\constants.py",
        r"c:\Users\leerg\OneDrive\Desktop\sales-os\backend\app\db\session.py",
        r"c:\Users\leerg\OneDrive\Desktop\sales-os\backend\app\db\base.py",
        r"c:\Users\leerg\OneDrive\Desktop\sales-os\backend\app\core\auth\__init__.py",
        r"c:\Users\leerg\OneDrive\Desktop\sales-os\backend\alembic\script.py.mako",
        r"c:\Users\leerg\OneDrive\Desktop\sales-os\frontend\types\index.ts",
        r"c:\Users\leerg\OneDrive\Desktop\sales-os\frontend\src\app\page.tsx",
        r"c:\Users\leerg\OneDrive\Desktop\sales-os\frontend\src\app\layout.tsx",
        r"c:\Users\leerg\OneDrive\Desktop\sales-os\frontend\src\app\globals.css",
    ]

    for f in files:
        if os.path.exists(f):
            resolve_file(f)
        else:
            print(f"Skipping missing file: {f}")
