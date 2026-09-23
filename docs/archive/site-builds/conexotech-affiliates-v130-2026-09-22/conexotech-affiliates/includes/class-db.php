<?php
/**
 * CXAF_DB — tabelas e consultas do rastreio nativo de afiliados (Fase 1).
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

class CXAF_DB {

	public static function table_links() {
		global $wpdb;
		return $wpdb->prefix . 'cxaf_links';
	}

	public static function table_clicks() {
		global $wpdb;
		return $wpdb->prefix . 'cxaf_clicks';
	}

	public static function init() {
		// Reexecuta o dbDelta quando a versão muda (ex.: Fase 2 adiciona colunas de status).
		if ( get_option( 'cxaf_version' ) !== CXAF_VERSION ) {
			self::activate();
		}
	}

	public static function activate() {
		global $wpdb;
		require_once ABSPATH . 'wp-admin/includes/upgrade.php';

		$charset = $wpdb->get_charset_collate();
		$links   = self::table_links();
		$clicks  = self::table_clicks();

		$sql_links = "CREATE TABLE {$links} (
			id bigint(20) unsigned NOT NULL AUTO_INCREMENT,
			slug varchar(100) NOT NULL,
			url text NOT NULL,
			loja varchar(40) NOT NULL DEFAULT '',
			produto varchar(190) NOT NULL DEFAULT '',
			post_id bigint(20) unsigned NOT NULL DEFAULT 0,
			status_code int(11) NOT NULL DEFAULT 0,
			status_msg varchar(190) NOT NULL DEFAULT '',
			verificado_em datetime NOT NULL DEFAULT '0000-00-00 00:00:00',
			criado_em datetime NOT NULL DEFAULT '0000-00-00 00:00:00',
			PRIMARY KEY  (id),
			UNIQUE KEY slug (slug),
			KEY post_id (post_id)
		) {$charset};";

		$sql_clicks = "CREATE TABLE {$clicks} (
			id bigint(20) unsigned NOT NULL AUTO_INCREMENT,
			link_id bigint(20) unsigned NOT NULL DEFAULT 0,
			ip_hash varchar(64) NOT NULL DEFAULT '',
			ua varchar(255) NOT NULL DEFAULT '',
			referrer text,
			criado_em datetime NOT NULL DEFAULT '0000-00-00 00:00:00',
			PRIMARY KEY  (id),
			KEY link_id (link_id),
			KEY criado_em (criado_em)
		) {$charset};";

		dbDelta( $sql_links );
		dbDelta( $sql_clicks );

		update_option( 'cxaf_version', CXAF_VERSION );
		// O flush das regras do /go/ acontece no admin_init (CXAF_Redirect::maybe_flush).
		update_option( 'cxaf_flush_rewrite', 1 );
	}

	public static function get_link_by_slug( $slug ) {
		global $wpdb;
		$slug = sanitize_title( $slug );
		if ( '' === $slug ) {
			return null;
		}
		return $wpdb->get_row(
			$wpdb->prepare( 'SELECT * FROM ' . self::table_links() . ' WHERE slug = %s LIMIT 1', $slug )
		);
	}

	public static function get_or_create_link( $slug, $url, $loja = '', $produto = '', $post_id = 0 ) {
		$slug = sanitize_title( $slug );
		$url  = esc_url_raw( trim( (string) $url ) );
		if ( '' === $slug || '' === $url ) {
			return null;
		}
		$found = self::get_link_by_slug( $slug );
		if ( $found ) {
			return $found;
		}
		global $wpdb;
		$wpdb->insert(
			self::table_links(),
			array(
				'slug'      => $slug,
				'url'       => $url,
				'loja'      => sanitize_text_field( $loja ),
				'produto'   => sanitize_text_field( $produto ),
				'post_id'   => absint( $post_id ),
				'criado_em' => current_time( 'mysql' ),
			),
			array( '%s', '%s', '%s', '%s', '%d', '%s' )
		);
		if ( ! $wpdb->insert_id ) {
			return null;
		}
		return self::get_link_by_slug( $slug );
	}

	public static function log_click( $link_id ) {
		global $wpdb;
		$ip = isset( $_SERVER['REMOTE_ADDR'] ) ? (string) $_SERVER['REMOTE_ADDR'] : ''; // phpcs:ignore
		$ua = isset( $_SERVER['HTTP_USER_AGENT'] ) ? substr( (string) $_SERVER['HTTP_USER_AGENT'], 0, 255 ) : ''; // phpcs:ignore
		$ref = wp_get_referer();
		$wpdb->insert(
			self::table_clicks(),
			array(
				'link_id'   => absint( $link_id ),
				'ip_hash'   => hash_hmac( 'sha256', $ip, wp_salt( 'auth' ) ),
				'ua'        => sanitize_text_field( $ua ),
				'referrer'  => $ref ? esc_url_raw( $ref ) : '',
				'criado_em' => current_time( 'mysql' ),
			),
			array( '%d', '%s', '%s', '%s', '%s' )
		);
	}

	protected static function threshold( $days ) {
		$days = max( 1, absint( $days ) );
		return date( 'Y-m-d H:i:s', strtotime( current_time( 'mysql' ) . " -{$days} days" ) );
	}

	public static function count_clicks( $days = 30 ) {
		global $wpdb;
		return (int) $wpdb->get_var(
			$wpdb->prepare(
				'SELECT COUNT(*) FROM ' . self::table_clicks() . ' WHERE criado_em >= %s',
				self::threshold( $days )
			)
		);
	}

	public static function clicks_by_day( $days = 14 ) {
		global $wpdb;
		$days = max( 1, min( 90, absint( $days ) ) );
		return $wpdb->get_results(
			$wpdb->prepare(
				'SELECT DATE(criado_em) AS dia, COUNT(*) AS total FROM ' . self::table_clicks() . ' WHERE criado_em >= %s GROUP BY dia ORDER BY dia DESC LIMIT %d',
				self::threshold( $days ),
				$days
			)
		);
	}

	public static function top_links( $days = 30, $limit = 10 ) {
		global $wpdb;
		$limit = max( 1, min( 50, absint( $limit ) ) );
		return $wpdb->get_results(
			$wpdb->prepare(
				'SELECT l.slug, l.produto, l.loja, COUNT(c.id) AS total FROM ' . self::table_clicks() . ' c INNER JOIN ' . self::table_links() . ' l ON l.id = c.link_id WHERE c.criado_em >= %s GROUP BY c.link_id ORDER BY total DESC LIMIT %d',
				self::threshold( $days ),
				$limit
			)
		);
	}

	public static function recent_clicks( $limit = 20 ) {
		global $wpdb;
		$limit = max( 1, min( 100, absint( $limit ) ) );
		return $wpdb->get_results(
			$wpdb->prepare(
				'SELECT c.criado_em, c.referrer, l.slug, l.produto, l.loja FROM ' . self::table_clicks() . ' c INNER JOIN ' . self::table_links() . ' l ON l.id = c.link_id ORDER BY c.id DESC LIMIT %d',
				$limit
			)
		);
	}

	public static function all_links( $limit = 200 ) {
		global $wpdb;
		$limit = max( 1, min( 500, absint( $limit ) ) );
		return $wpdb->get_results(
			$wpdb->prepare( 'SELECT * FROM ' . self::table_links() . ' ORDER BY id DESC LIMIT %d', $limit )
		);
	}

	public static function update_link_status( $link_id, $code, $msg = '' ) {
		global $wpdb;
		return $wpdb->update(
			self::table_links(),
			array(
				'status_code'   => absint( $code ),
				'status_msg'    => substr( sanitize_text_field( $msg ), 0, 190 ),
				'verificado_em' => current_time( 'mysql' ),
			),
			array( 'id' => absint( $link_id ) ),
			array( '%d', '%s', '%s' ),
			array( '%d' )
		);
	}

	public static function links_for_check( $limit = 50 ) {
		global $wpdb;
		$limit = max( 1, min( 100, absint( $limit ) ) );
		return $wpdb->get_results(
			$wpdb->prepare( 'SELECT * FROM ' . self::table_links() . ' ORDER BY verificado_em ASC LIMIT %d', $limit )
		);
	}

	public static function broken_links( $limit = 20 ) {
		global $wpdb;
		$limit = max( 1, min( 100, absint( $limit ) ) );
		return $wpdb->get_results(
			$wpdb->prepare(
				'SELECT * FROM ' . self::table_links() . " WHERE verificado_em > '0000-00-00 00:00:00' AND ( status_code = 0 OR status_code >= 400 ) ORDER BY verificado_em DESC LIMIT %d",
				$limit
			)
		);
	}
}
