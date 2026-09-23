<?php
/**
 * CXAF_Redirect — endpoint /go/{slug}: registra o clique e redireciona (302).
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

class CXAF_Redirect {

	public static function init() {
		add_action( 'init', array( __CLASS__, 'rewrite' ) );
		add_filter( 'query_vars', array( __CLASS__, 'query_vars' ) );
		add_action( 'template_redirect', array( __CLASS__, 'handle' ) );
		add_action( 'admin_init', array( __CLASS__, 'maybe_flush' ) );
	}

	public static function rewrite() {
		add_rewrite_rule( '^go/([^/]+)/?$', 'index.php?cxaf_go=$matches[1]', 'top' );
	}

	public static function query_vars( $vars ) {
		$vars[] = 'cxaf_go';
		return $vars;
	}

	public static function maybe_flush() {
		if ( get_option( 'cxaf_flush_rewrite' ) ) {
			flush_rewrite_rules();
			delete_option( 'cxaf_flush_rewrite' );
		}
	}

	public static function handle() {
		$slug = get_query_var( 'cxaf_go' );
		if ( '' === (string) $slug ) {
			return;
		}
		$link = CXAF_DB::get_link_by_slug( $slug );
		if ( ! $link || '' === (string) $link->url ) {
			global $wp_query;
			$wp_query->set_404();
			status_header( 404 );
			$tpl = get_404_template();
			if ( $tpl ) {
				include $tpl;
			} else {
				wp_die( 'Link de afiliado não encontrado.', 'Não encontrado', 404 );
			}
			exit;
		}
		CXAF_DB::log_click( $link->id );
		wp_redirect( $link->url, 302 );
		exit;
	}
}
