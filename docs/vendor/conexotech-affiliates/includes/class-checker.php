<?php
/**
 * CXAF_Checker — Fase 2: verifica links afiliados (cron diário + botão manual).
 *
 * Quebrado = erro de conexão/timeout (código 0) ou HTTP >= 400.
 * Redirects 301/302 são seguidos automaticamente e NÃO contam como quebra.
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

class CXAF_Checker {

	const CRON_HOOK = 'cxaf_daily_check';

	public static function init() {
		add_action( 'init', array( __CLASS__, 'schedule' ) );
		add_action( self::CRON_HOOK, array( __CLASS__, 'run_cron' ) );
		add_action( 'admin_post_cxaf_check_now', array( __CLASS__, 'handle_manual' ) );
	}

	public static function schedule() {
		if ( ! wp_next_scheduled( self::CRON_HOOK ) ) {
			wp_schedule_event( time() + HOUR_IN_SECONDS, 'daily', self::CRON_HOOK );
		}
	}

	public static function deactivate() {
		wp_clear_scheduled_hook( self::CRON_HOOK );
	}

	public static function run_cron() {
		self::run( 50 );
	}

	public static function handle_manual() {
		if ( ! current_user_can( 'manage_options' ) ) {
			wp_die( 'Sem permissão.' );
		}
		check_admin_referer( 'cxaf_check_now' );
		$total = self::run( 30 );
		wp_safe_redirect( add_query_arg( 'cxaf_checked', $total, admin_url( 'admin.php?page=cxaf-dashboard' ) ) );
		exit;
	}

	public static function run( $limit = 50 ) {
		$links = CXAF_DB::links_for_check( $limit );
		$n = 0;
		foreach ( $links as $link ) {
			self::check_one( $link );
			$n++;
		}
		return $n;
	}

	protected static function check_one( $link ) {
		$host = strtolower( (string) wp_parse_url( $link->url, PHP_URL_HOST ) );
		if ( 'youtube.com' === $host || substr( $host, -12 ) === '.youtube.com' || 'youtu.be' === $host ) {
			self::check_youtube( $link );
			return;
		}
		$res = wp_remote_head(
			$link->url,
			array(
				'timeout'     => 8,
				'redirection' => 3,
				'user-agent'  => 'ConexoTech-LinkChecker/1.1',
			)
		);
		if ( is_wp_error( $res ) ) {
			CXAF_DB::update_link_status( $link->id, 0, $res->get_error_message() );
			return;
		}
		$code = (int) wp_remote_retrieve_response_code( $res );
		if ( $code >= 200 && $code < 400 ) {
			$msg = 'OK';
		} else {
			$msg = 'HTTP ' . $code;
		}
		CXAF_DB::update_link_status( $link->id, $code, $msg );
	}

	protected static function check_youtube( $link ) {
		// Watch pages bloqueiam robôs com frequência; o oEmbed diz a verdade:
		// 200 = vídeo existe e pode ser incorporado; erro/4xx = removido/privado.
		$res = wp_remote_get(
			'https://www.youtube.com/oembed?url=' . rawurlencode( $link->url ) . '&format=json',
			array(
				'timeout'    => 8,
				'user-agent' => 'ConexoTech-LinkChecker/1.2',
			)
		);
		if ( is_wp_error( $res ) ) {
			CXAF_DB::update_link_status( $link->id, 0, $res->get_error_message() );
			return;
		}
		$code = (int) wp_remote_retrieve_response_code( $res );
		if ( 200 === $code ) {
			CXAF_DB::update_link_status( $link->id, 200, 'OK (YouTube)' );
		} else {
			CXAF_DB::update_link_status( $link->id, $code, 'Vídeo indisponível no YouTube' );
		}
	}
}
