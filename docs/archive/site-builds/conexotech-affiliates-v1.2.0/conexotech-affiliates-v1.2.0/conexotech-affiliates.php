<?php
/**
 * Plugin Name: ConexoTech Afiliados — Rastreio Nativo
 * Plugin URI:  https://conexotech.com.br
 * Description: Rastreio nativo de cliques em links de afiliados: endpoint /go/slug, dashboard no admin e shortcode [affiliate_button]. Sem dependência de terceiros.
 * Version:     1.2.0
 * Author:      ConexoTech
 * Text Domain: conexotech-affiliates
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

define( 'CXAF_VERSION', '1.2.0' );
define( 'CXAF_DIR', plugin_dir_path( __FILE__ ) );
define( 'CXAF_URL', plugin_dir_url( __FILE__ ) );

require_once CXAF_DIR . 'includes/class-db.php';
require_once CXAF_DIR . 'includes/class-redirect.php';
require_once CXAF_DIR . 'includes/class-admin.php';
require_once CXAF_DIR . 'includes/class-shortcode.php';
require_once CXAF_DIR . 'includes/class-checker.php';

register_activation_hook( __FILE__, array( 'CXAF_DB', 'activate' ) );
register_deactivation_hook( __FILE__, array( 'CXAF_Checker', 'deactivate' ) );

add_action( 'plugins_loaded', function () {
	CXAF_DB::init();
	CXAF_Redirect::init();
	CXAF_Admin::init();
	CXAF_Shortcode::init();
	CXAF_Checker::init();
} );
