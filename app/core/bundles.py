import os

from flask_assets import Bundle

from ..utils.functions import recursive_flatten_iterator


def get_bundle(route, tpl, ext, paths, type=False):
    if route and tpl and ext:
        return {
            'instance': Bundle(*paths, output=get_path(route, tpl, ext, type), filters=get_filter(ext)),
            'name': get_filename(route, tpl, ext, type),
            'dir': os.getcwd()
        }



def register_bundle(assets, bundle):
    assets.register(bundle['name'], bundle['instance'])
    return f" Bundle {bundle['name']} registered successfully!"


def register_bundles(assets, bundles):
    for x in recursive_flatten_iterator(bundles):
        for bundle in x:
            register_bundle(assets, bundle)


def get_filename(route, tpl, ext, type):
    if type:
        return f"{route}_{tpl}_{ext}_defer"
    else:
        return f"{route}_{tpl}_{ext}"


def get_path(route, tpl, ext, type):
    if type:
        return f"gen/{route}/{tpl}/defer.{ext}"
    else:
        return f"gen/{route}/{tpl}/main.{ext}"


def get_filter(ext):
    return f"{ext}min"


bundles = {
    "application": {
        "core": {
            "js": [get_bundle('application', 'core', 'js', [
                'js/blocks/js_utils.js',
                'js/blocks/js_application_core.js'
            ])]
        },
        "index": {
            "css": [get_bundle('application', 'index', 'css', [
                'css/blocks/blog.css'
            ])],
            "js": [get_bundle('application', 'index', 'js', [
                'js/libs/bootstrap.bundle.min.js'
            ])]
        },
        "all": {
            "css": [get_bundle('application', 'all', 'css', [
                'css/blocks/table.css',
                'css/blocks/dashboard.css'
            ])],
            "js": [get_bundle('application', 'all', 'js', [
                'js/libs/bootstrap.bundle.min.js',
                'js/blocks/js_table.js',
                'js/blocks/js_table_websocket.js',
                'js/libs/fontawesome.all.min.js',
                'js/app.js'
            ])]
        },
        "forms": {
            "css": [get_bundle('application', 'forms', 'css', [
                'css/blocks/address.css',
                'css/blocks/select.css',
                'css/blocks/checkbox.css'
            ])],
            "js": [get_bundle('application', 'forms', 'js', [
                'js/libs/bootstrap.bundle.min.js',
                'js/libs/select2.min.js',
                'js/app.js'
            ])]
        },
        "dashboard": {
            "css": [get_bundle('application', 'dashboard', 'css', ['css/blocks/dashboard.css'])],
            "js": [get_bundle('application', 'dashboard', 'js', [
                'js/libs/bootstrap.bundle.min.js',
                'js/blocks/js_table.js', 
                'js/libs/fontawesome.all.min.js',
                'js/libs/chart.min.js',
                'js/blocks/js_dashboard_ajax.js',
                'js/app.js'
            ])]
        },
        "create": {
            "css": [get_bundle('application', 'create', 'css', [
                'css/blocks/address.css',
                'css/blocks/select.css',
                'css/blocks/loading.css'
            ])],
            "js": [get_bundle('application', 'create', 'js', [
                'js/libs/bootstrap.bundle.min.js',
                'js/libs/select2.min.js',
                'js/blocks/js_utils.js',
                'js/blocks/js_application_core.js',
                'js/app.js'
            ])]
        },
        "update": {
            "css": [get_bundle('application', 'update', 'css', [
                'css/blocks/address.css',
                'css/blocks/select.css',
                'css/blocks/loading.css'
            ])],
            "js": [get_bundle('application', 'update', 'js', [
                'js/libs/bootstrap.bundle.min.js',
                'js/libs/select2.min.js',
                'js/blocks/js_utils.js',
                'js/blocks/js_application_core.js',
                'js/app.js'
            ])]
        },
        "admin": {
            "css": [get_bundle('application', 'admin', 'css', ['css/blocks/table.css', 'css/blocks/dashboard.css'])],
            "js": [get_bundle('application', 'admin', 'js', ['js/libs/bootstrap.bundle.min.js','js/blocks/js_table.js', 'js/libs/fontawesome.all.min.js', 'js/blocks/js_utils.js',
                'js/blocks/js_application_core.js',
                'js/app.js', 'js/libs/chart.min.js'])]
        },
        "users": {
            "css": [get_bundle('application', 'users', 'css', ['css/blocks/table.css', 'css/blocks/dashboard.css'])],
            "js": [get_bundle('application', 'users', 'js', ['js/libs/bootstrap.bundle.min.js','js/blocks/js_table.js', 'js/libs/fontawesome.all.min.js','js/blocks/js_utils.js',
                'js/blocks/js_application_core.js',
                'js/app.js'])]
        },
        "add_data": {
            "js": [get_bundle('application', 'add_data', 'js', [
                'js/libs/bootstrap.bundle.min.js',
                'js/libs/select2.min.js',
                'js/blocks/js_utils.js',
                'js/blocks/js_application_core.js',
                'js/app.js'
            ])]
        },

        
        
        
    },
    "user": {
        "update": {
            "css": [get_bundle('user', 'update', 'css', [
                'css/blocks/dashboard.css'
            ])],
            "js": [get_bundle('user', 'update', 'js', [
                'js/libs/bootstrap.bundle.min.js',
                'js/blocks/js_update.js'
            ])]
        },
        "register": {
            "css": [get_bundle('user', 'register', 'css', [
                'css/blocks/dashboard.css'
            ])],
            "js": [get_bundle('user', 'register', 'js', [
                'js/libs/bootstrap.bundle.min.js',
                'js/blocks/js_register.js'
            ])]
        }
    },
    "blog": {
        "blog": {
            "css": [get_bundle('blog', 'blog', 'css', [
                'css/blocks/blog.css'
            ])],
            "js": [get_bundle('blog', 'blog', 'js', [
                'js/libs/bootstrap.bundle.min.js'
            ])]
        },
    }
}