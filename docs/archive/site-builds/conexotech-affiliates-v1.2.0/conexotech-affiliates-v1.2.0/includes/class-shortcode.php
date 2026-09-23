<?php
/**
 * CXAF_Shortcode — [affiliate_button produto="" loja="" url="" texto="" slug=""].
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

class CXAF_Shortcode {

	public static function init() {
		add_shortcode( 'affiliate_button', array( __CLASS__, 'render' ) );
	}

	public static function render( $atts ) {
		$atts = shortcode_atts(
			array(
				'produto' => '',
				'loja'    => 'amazon',
				'url'     => '',
				'texto'   => 'Ver melhor preço',
				'slug'    => '',
			),
			$atts,
			'affiliate_button'
		);
		$url = esc_url_raw( trim( (string) $atts['url'] ) );
		if ( '' === $url ) {
			return '';
		}
		$slug = '' !== trim( (string) $atts['slug'] )
			? sanitize_title( $atts['slug'] )
			: sanitize_title( trim( (string) $atts['produto'] ) . '-' . trim( (string) $atts['loja'] ) );
		if ( '' === $slug ) {
			$slug = 'link';
		}
		$link = CXAF_DB::get_or_create_link(
			$slug,
			$url,
			sanitize_text_field( $atts['loja'] ),
			sanitize_text_field( $atts['produto'] ),
			get_the_ID() ? (int) get_the_ID() : 0
		);
		if ( ! $link ) {
			return '';
		}
		$go = home_url( '/go/' . $link->slug );
		return sprintf(
			'<a class="cxaf-affiliate-btn" href="%s" target="_blank" rel="sponsored nofollow noopener">%s</a>',
			esc_url( $go ),
			esc_html( $atts['texto'] )
		);
	}
}
