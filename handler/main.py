# from handler.constants import CUSTOM_LABEL, UNAVAILABLE_OFFER_ID_LIST
from handler.decorators import time_of_function, time_of_script
from handler.utils import initialize_components, save_to_database


@time_of_script
@time_of_function
def main():
    saver, handler_client, db_client, image_client = initialize_components()
    saver.save_xml()
    data = handler_client.get_offers_report()
    save_to_database(db_client, data)
    # handler_client.process_feeds(CUSTOM_LABEL, UNAVAILABLE_OFFER_ID_LIST)
    # handler_client.full_outer_join_feeds()
    # handler_client.inner_join_feeds()
    image_client.get_images()
    image_client.add_frame()
    handler_client.image_replacement()


if __name__ == '__main__':
    main()
