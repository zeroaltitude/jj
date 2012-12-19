BEGIN;
DROP TABLE IF EXISTS `jjmaker_mold`;
DROP TABLE IF EXISTS `jjmaker_pagetemplateposition`;
DROP TABLE IF EXISTS `jjmaker_activity`;
DROP TABLE IF EXISTS `jjmaker_journalmessage`;
DROP TABLE IF EXISTS `jjmaker_journalphoto`;
DROP TABLE IF EXISTS `jjmaker_journalitem`;
DROP TABLE IF EXISTS `jjmaker_quadrant`;
DROP TABLE IF EXISTS `jjmaker_positionalthing`;
DROP TABLE IF EXISTS `jjmaker_gravity`;
DROP TABLE IF EXISTS `jjmaker_pagetemplategravity`;
DROP TABLE IF EXISTS `jjmaker_journalpage`;
DROP TABLE IF EXISTS `jjmaker_pagestyle`;
DROP TABLE IF EXISTS `jjmaker_pagetemplate`;
DROP TABLE IF EXISTS `jjmaker_journaltemplate`;
DROP TABLE IF EXISTS `jjmaker_journal`;
DROP TABLE IF EXISTS `jjmaker_unsubscriber`;
DROP TABLE IF EXISTS `jjmaker_userprofile`;
DROP TABLE IF EXISTS `jjmaker_coupon`;
CREATE TABLE `jjmaker_userprofile` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `fb_id` varchar(64) NOT NULL UNIQUE,
    `fb_fname` varchar(64) NOT NULL,
    `fb_lname` varchar(64) NOT NULL,
    `fb_name` varchar(132) NOT NULL,
    `fb_url` varchar(1024),
    `token` varchar(256),
    `email` varchar(256)
)
;
CREATE TABLE `jjmaker_product` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `name` varchar(128) NOT NULL,
    `price` numeric(6, 2) NOT NULL,
    `line_description` varchar(1024),
    `full_description` varchar(1024)
)
;
CREATE TABLE `jjmaker_shipping` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `firstname` varchar(64) NOT NULL,
    `middlename` varchar(64),
    `lastname` varchar(64) NOT NULL,
    `addr1` varchar(128) NOT NULL,
    `addr2` varchar(128),
    `city` varchar(128) NOT NULL,
    `state` varchar(128) NOT NULL,
    `zip` varchar(128) NOT NULL,
    `country` varchar(128) NOT NULL,
    `telephone` varchar(64) NOT NULL
)
;
CREATE TABLE `jjmaker_coupon` (
     `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
     `ctype` varchar(4) NOT NULL,
     `amount` numeric(6, 2) NOT NULL,
     `code` varchar(64) NOT NULL
)
;
CREATE TABLE `jjmaker_order` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `user_id` integer NOT NULL,
    `product_id` integer NOT NULL,
    `shipping_id` integer NOT NULL,
    `quantity` integer NOT NULL,
    `journal_id` integer NOT NULL,
    `created` datetime NOT NULL,
    `status` varchar(64) NOT NULL,
    `ccauth` varchar(128),
    `notes` varchar(1024),
    `unitprice` numeric(6,2),
    `shippingprice` numeric(6,2),
    `tax` numeric(6,2),
    `coupon_id` integer
)
;
ALTER TABLE `jjmaker_order` ADD CONSTRAINT `user_id_refs_id_78c89d31` FOREIGN KEY (`user_id`) REFERENCES `jjmaker_userprofile` (`id`);
ALTER TABLE `jjmaker_order` ADD CONSTRAINT `product_id_refs_id_d4bfba52` FOREIGN KEY (`product_id`) REFERENCES `jjmaker_product` (`id`);
ALTER TABLE `jjmaker_order` ADD CONSTRAINT `shipping_id_refs_id_42932eb0` FOREIGN KEY (`shipping_id`) REFERENCES `jjmaker_shipping` (`id`);
CREATE TABLE `jjmaker_unsubscriber` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `email` varchar(128) NOT NULL UNIQUE
)
;
CREATE TABLE `jjmaker_journal` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `user_id` integer NOT NULL,
    `created` datetime NOT NULL,
    `title` varchar(1024) NOT NULL,
    `subtitle` varchar(1024),
    `status` varchar(64) NOT NULL,
    `page_count` integer NOT NULL,
    `date_range_start` datetime,
    `date_range_end` datetime
)
;
ALTER TABLE `jjmaker_journal` ADD CONSTRAINT `user_id_refs_id_8339c94a` FOREIGN KEY (`user_id`) REFERENCES `jjmaker_userprofile` (`id`);
CREATE TABLE `jjmaker_journaltemplate` (
    `journal_ptr_id` integer NOT NULL PRIMARY KEY,
    `template_title` varchar(128) NOT NULL
)
;
ALTER TABLE `jjmaker_journaltemplate` ADD CONSTRAINT `journal_ptr_id_refs_id_7df3c937` FOREIGN KEY (`journal_ptr_id`) REFERENCES `jjmaker_journal` (`id`);
CREATE TABLE `jjmaker_pagetemplate` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `aspect_base_x` numeric(9, 7) NOT NULL,
    `aspect_base_y` numeric(9, 7) NOT NULL,
    `outer_margin_top` numeric(9, 7) NOT NULL,
    `outer_margin_right` numeric(9, 7) NOT NULL,
    `outer_margin_bottom` numeric(9, 7) NOT NULL,
    `outer_margin_left` numeric(9, 7) NOT NULL,
    `inner_margin_width` numeric(9, 7) NOT NULL,
    `inner_margin_height` numeric(9, 7) NOT NULL,
    `total_photos` integer NOT NULL,
    `total_texts` integer NOT NULL,
    `description` varchar(1024) NOT NULL
)
;
CREATE TABLE `jjmaker_pagestyle` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `background_image` varchar(1024),
    `background_color` varchar(32),
    `text_color` varchar(32),
    `text_font` varchar(32),
    `text_size` varchar(32),
    `box_color` varchar(32),
    `text_box_margin` numeric(9, 7)
)
;
CREATE TABLE `jjmaker_journalpage` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `journal_id` integer NOT NULL,
    `page_template_id` integer NOT NULL,
    `page_style_id` integer NOT NULL,
    `page_number` integer NOT NULL
)
;
ALTER TABLE `jjmaker_journalpage` ADD CONSTRAINT `journal_id_refs_id_4a1b66b0` FOREIGN KEY (`journal_id`) REFERENCES `jjmaker_journal` (`id`);
ALTER TABLE `jjmaker_journalpage` ADD CONSTRAINT `page_template_id_refs_id_5512d05d` FOREIGN KEY (`page_template_id`) REFERENCES `jjmaker_pagetemplate` (`id`);
ALTER TABLE `jjmaker_journalpage` ADD CONSTRAINT `page_style_id_refs_id_b1153701` FOREIGN KEY (`page_style_id`) REFERENCES `jjmaker_pagestyle` (`id`);
CREATE TABLE `jjmaker_pagetemplategravity` (
    `pagetemplate_ptr_id` integer NOT NULL PRIMARY KEY,
    `grid_width` integer NOT NULL,
    `grid_height` integer NOT NULL
)
;
ALTER TABLE `jjmaker_pagetemplategravity` ADD CONSTRAINT `pagetemplate_ptr_id_refs_id_a512e4fa` FOREIGN KEY (`pagetemplate_ptr_id`) REFERENCES `jjmaker_pagetemplate` (`id`);
CREATE TABLE `jjmaker_gravity` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `orientation` varchar(32) NOT NULL,
    `metadata` varchar(1024) NOT NULL
)
;
CREATE TABLE `jjmaker_positionalthing` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `page_template_id` integer NOT NULL
)
;
ALTER TABLE `jjmaker_positionalthing` ADD CONSTRAINT `page_template_id_refs_id_f6ce6c9` FOREIGN KEY (`page_template_id`) REFERENCES `jjmaker_pagetemplate` (`id`);
CREATE TABLE `jjmaker_quadrant` (
    `positionalthing_ptr_id` integer NOT NULL PRIMARY KEY,
    `coordinate_x` integer NOT NULL,
    `units_x` integer NOT NULL,
    `coordinate_y` integer NOT NULL,
    `units_y` integer NOT NULL,
    `grid_gravity_x_id` integer NOT NULL,
    `grid_gravity_y_id` integer NOT NULL,
    `background_color` varchar(32),
    `text_color` varchar(32),
    `content_type` varchar(32)
)
;
ALTER TABLE `jjmaker_quadrant` ADD CONSTRAINT `positionalthing_ptr_id_refs_id_dc80aa14` FOREIGN KEY (`positionalthing_ptr_id`) REFERENCES `jjmaker_positionalthing` (`id`);
ALTER TABLE `jjmaker_quadrant` ADD CONSTRAINT `grid_gravity_x_id_refs_id_97ae1bdc` FOREIGN KEY (`grid_gravity_x_id`) REFERENCES `jjmaker_gravity` (`id`);
ALTER TABLE `jjmaker_quadrant` ADD CONSTRAINT `grid_gravity_y_id_refs_id_97ae1bdc` FOREIGN KEY (`grid_gravity_y_id`) REFERENCES `jjmaker_gravity` (`id`);
CREATE TABLE `jjmaker_journalitem` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `journal_page_id` integer NOT NULL,
    `positional_thing_id` integer NOT NULL,
    `fb_id` varchar(32) NOT NULL,
    `fb_url` varchar(1024) NOT NULL,
    `item_date` datetime NOT NULL,
    `item_visibility_state` varchar(32) NOT NULL,
    `item_type` varchar(32) NOT NULL,
    `event_id` integer NOT NULL,
    `score` integer NOT NULL
)
;
ALTER TABLE `jjmaker_journalitem` ADD CONSTRAINT `journal_page_id_refs_id_d24ea44b` FOREIGN KEY (`journal_page_id`) REFERENCES `jjmaker_journalpage` (`id`);
ALTER TABLE `jjmaker_journalitem` ADD CONSTRAINT `positional_thing_id_refs_id_fb2730ed` FOREIGN KEY (`positional_thing_id`) REFERENCES `jjmaker_positionalthing` (`id`);
CREATE TABLE `jjmaker_journalphoto` (
    `journalitem_ptr_id` integer NOT NULL PRIMARY KEY,
    `dimension_x` integer NOT NULL,
    `dimension_y` integer NOT NULL,
    `fb_picture` varchar(1024) NOT NULL,
    `fb_source` varchar(1024) NOT NULL
)
;
ALTER TABLE `jjmaker_journalphoto` ADD CONSTRAINT `journalitem_ptr_id_refs_id_3469bd29` FOREIGN KEY (`journalitem_ptr_id`) REFERENCES `jjmaker_journalitem` (`id`);
CREATE TABLE `jjmaker_journalmessage` (
    `journalitem_ptr_id` integer NOT NULL PRIMARY KEY,
    `length_chars` integer NOT NULL,
    `message` varchar(1024) NOT NULL
)
;
ALTER TABLE `jjmaker_journalmessage` ADD CONSTRAINT `journalitem_ptr_id_refs_id_d1df4106` FOREIGN KEY (`journalitem_ptr_id`) REFERENCES `jjmaker_journalitem` (`id`);
CREATE TABLE `jjmaker_activity` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `user_id` integer NOT NULL,
    `atype` varchar(100) NOT NULL,
    `occurred` datetime NOT NULL,
    `metadata` varchar(1024) NOT NULL,
    `foreign_type` varchar(64) NOT NULL,
    `foreign_id` integer NOT NULL
)
;
ALTER TABLE `jjmaker_activity` ADD CONSTRAINT `user_id_refs_id_e2c8c40d` FOREIGN KEY (`user_id`) REFERENCES `jjmaker_userprofile` (`id`);
CREATE TABLE `jjmaker_pagetemplateposition` (
    `pagetemplate_ptr_id` integer NOT NULL PRIMARY KEY,
    `mold_count` integer NOT NULL
)
;
ALTER TABLE `jjmaker_pagetemplateposition` ADD CONSTRAINT `pagetemplate_ptr_id_refs_id_f9c03b32` FOREIGN KEY (`pagetemplate_ptr_id`) REFERENCES `jjmaker_pagetemplate` (`id`);
CREATE TABLE `jjmaker_mold` (
    `positionalthing_ptr_id` integer NOT NULL PRIMARY KEY,
    `offset_top` numeric(9, 7) NOT NULL,
    `offset_left` numeric(9, 7) NOT NULL,
    `width` numeric(9, 7) NOT NULL,
    `height` numeric(9, 7) NOT NULL,
    `mtype` varchar(32) NOT NULL
)
;
ALTER TABLE `jjmaker_mold` ADD CONSTRAINT `positionalthing_ptr_id_refs_id_2b58688` FOREIGN KEY (`positionalthing_ptr_id`) REFERENCES `jjmaker_positionalthing` (`id`);
CREATE INDEX `jjmaker_order_user_id` ON `jjmaker_order` (`user_id`);
CREATE INDEX `jjmaker_order_product_id` ON `jjmaker_order` (`product_id`);
CREATE INDEX `jjmaker_order_shipping_id` ON `jjmaker_order` (`shipping_id`);
CREATE INDEX `jjmaker_journal_user_id` ON `jjmaker_journal` (`user_id`);
CREATE INDEX `jjmaker_journalpage_journal_id` ON `jjmaker_journalpage` (`journal_id`);
CREATE INDEX `jjmaker_journalpage_page_template_id` ON `jjmaker_journalpage` (`page_template_id`);
CREATE INDEX `jjmaker_journalpage_page_style_id` ON `jjmaker_journalpage` (`page_style_id`);
CREATE INDEX `jjmaker_positionalthing_page_template_id` ON `jjmaker_positionalthing` (`page_template_id`);
CREATE INDEX `jjmaker_quadrant_grid_gravity_x_id` ON `jjmaker_quadrant` (`grid_gravity_x_id`);
CREATE INDEX `jjmaker_quadrant_grid_gravity_y_id` ON `jjmaker_quadrant` (`grid_gravity_y_id`);
CREATE INDEX `jjmaker_journalitem_journal_page_id` ON `jjmaker_journalitem` (`journal_page_id`);
CREATE INDEX `jjmaker_journalitem_positional_thing_id` ON `jjmaker_journalitem` (`positional_thing_id`);
CREATE INDEX `jjmaker_activity_user_id` ON `jjmaker_activity` (`user_id`);
COMMIT;
