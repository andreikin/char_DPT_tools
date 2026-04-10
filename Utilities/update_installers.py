import os


def update_directory(directory):

    target_names = (
        'menu_installer.py',
        'shelf_installer.py',
        'button_installer.py'
    )

    current_file = os.path.abspath(r"D:\Projects\Python\char_dpt_tools\Utilities\base_installer.py")

    with open(current_file, 'rb') as f:
        current_content = f.read()
    for root, dirs, files in os.walk(directory):
        for filename in files:
            if filename in target_names:
                target_path = os.path.join(root, filename)
                try:
                    with open(target_path, 'wb') as f:
                        f.write(current_content)

                    print('Updated: {}'.format(target_path))

                except Exception as e:
                    print('Failed to update {}: {}'.format(target_path, e))


if __name__ == '__main__':
    update_directory(r'D:\Projects\Python\char_dpt_tools\Char_DPT_tools')
    update_directory(r'D:\Projects\Python\char_dpt_tools\Char_DPT_shelf')
    update_directory(r'D:\Projects\Python\char_dpt_tools\Utilities\script_template')