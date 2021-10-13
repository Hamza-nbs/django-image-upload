from PIL import Image
from io import BytesIO
from django.core.files.images import ImageFile
from requests import Session
from ImageUploaderBackEnd.settings import ACUMATICA_SIGN_IN_URL, ACUMATICA_CREDENTIALS,\
    ACUMATICA_UPLOAD_ENDPOINT, ACUMATICA_SIGN_OUT_URL


def get_upload_endpoint(acumatica):
    args = [ACUMATICA_UPLOAD_ENDPOINT]
    if acumatica.serial_number is not None:
        args += ['SerialAttributeScreen', acumatica.serial_number]
    else:
        args.append('StockItem')
    args.append(acumatica.inventory_id)
    return '/'.join(args)


def put_acumatica_images(session, endpoint, acumatica):
    inserted_data = {}
    for attr, api_field in (('large', 'LargeImage'), ('icon', 'IconImage')):
        attr_obj = getattr(acumatica, attr, None)
        if attr_obj:
            _, name = attr_obj.name.rsplit('/', 1)
            session.put(url=endpoint + '/files/' + name,
                        data=attr_obj.read(),
                        headers={'Content-Type': 'application/octet-stream'})
            inserted_data[api_field] = {'value': name}
    return inserted_data


def put_web_views(session, endpoint, web):
    inserted_data = {}
    for web_view in web.all():
        _, name = web_view.original.name.rsplit('/', 1)
        # session.put(url=endpoint + '/files/' + name,
        #             data=web_view.original.read(),
        #             headers={'Content-Type': 'application/octet-stream'})
        inserted_data[f'WebView{web_view.index}'] = {'value': name}
    return inserted_data


def push_to_acumatica(instance):
    if hasattr(instance, 'acumatica'):
        acumatica = instance.acumatica
        acumatica_input = {"InventoryID": {"value": acumatica.inventory_id}}
        if acumatica.serial_number:
            acumatica_input["LotSerialNbr"] = {"value": acumatica.serial_number}
        with Session() as session:
            print(session.post(ACUMATICA_SIGN_IN_URL, data=ACUMATICA_CREDENTIALS).status_code)
            endpoint = get_upload_endpoint(acumatica)
            inserted_acumatica = put_acumatica_images(session, endpoint, acumatica)
            inserted_web = put_web_views(session, endpoint, instance.web)
            put_data_type = '/SerialAttributeScreen' if "LotSerialNbr" in acumatica_input else '/StockItem'
            session.put(ACUMATICA_UPLOAD_ENDPOINT + put_data_type,
                        json={**acumatica_input, **inserted_acumatica, **inserted_web},
                        headers={'Content-Type': 'application/json'})
            session.post(ACUMATICA_SIGN_OUT_URL)


def get_name_extension(name):
    if '.' in name:
        dot_index = name.rfind('.')
    else:
        dot_index = len(name)
    return name[dot_index:]


def modify_n_get(image, name, width, height, name_suffix):
    if image is None:
        return None
    pillow_image = Image.open(image)
    pillow_image.thumbnail((width, height), Image.LANCZOS)
    image_bytes = BytesIO()
    pillow_image.save(image_bytes, pillow_image.format, quality=80, subsampling=0, optimize=True, progressive=True,
                      icc_profile=pillow_image.info.get('icc_profile', ''))
    dot_index = image.name.rfind('.') if '.' in image.name else len(name)
    if name is None:
        name = image.name[:dot_index]
    extension = image.name[dot_index:]
    return ImageFile(image_bytes, name + '-' + name_suffix + extension)
