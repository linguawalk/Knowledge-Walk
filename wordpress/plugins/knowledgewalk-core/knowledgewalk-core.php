<?php
/**
 * Plugin Name: KnowledgeWalk Core
 * Description: Encyclopedia articles and hierarchical knowledge topics for KnowledgeWalk.
 * Version: 0.1.0
 * Requires PHP: 7.4
 * Text Domain: knowledgewalk-core
 */

if (!defined('ABSPATH')) {
    exit;
}

function knowledgewalk_register_content_types() {
    register_post_type('kw_article', array(
        'labels' => array(
            'name' => '백과사전 문서',
            'singular_name' => '백과사전 문서',
            'add_new_item' => '새 백과사전 문서',
            'edit_item' => '백과사전 문서 편집',
        ),
        'public' => true,
        'show_in_rest' => true,
        'has_archive' => true,
        'rewrite' => array('slug' => 'encyclopedia', 'with_front' => false),
        'menu_icon' => 'dashicons-book-alt',
        'supports' => array('title', 'editor', 'excerpt', 'thumbnail', 'revisions', 'author'),
    ));

    register_taxonomy('kw_topic', array('kw_article'), array(
        'labels' => array(
            'name' => '지식 분류',
            'singular_name' => '지식 분류',
            'add_new_item' => '새 지식 분류',
        ),
        'public' => true,
        'hierarchical' => true,
        'show_in_rest' => true,
        'show_admin_column' => true,
        'rewrite' => array('slug' => 'topics', 'hierarchical' => true, 'with_front' => false),
    ));
}
add_action('init', 'knowledgewalk_register_content_types');

function knowledgewalk_activate() {
    knowledgewalk_register_content_types();
    flush_rewrite_rules();
}
register_activation_hook(__FILE__, 'knowledgewalk_activate');

function knowledgewalk_deactivate() {
    flush_rewrite_rules();
}
register_deactivation_hook(__FILE__, 'knowledgewalk_deactivate');
