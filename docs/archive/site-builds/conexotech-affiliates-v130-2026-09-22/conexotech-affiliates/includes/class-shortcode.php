<?php
/**
 * CXAF_Shortcode — [affiliate_button produto="" loja="" url="" texto="" slug=""]
 * e [affiliate_box tipo="box|pros|cta" ...].
 *
 * Regras: sem URL real não há botão (nunca CTA morto); tudo escapado;
 * links sempre sponsored+nofollow; clique rastreado via /go/.
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

class CXAF_Shortcode {

	public static function init() {
		add_shortcode( 'affiliate_button', array( __CLASS__, 'render' ) );
		add_shortcode( 'affiliate_box', array( __CLASS__, 'render_box' ) );
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

	public static function render_box( $atts ) {
		$atts = shortcode_atts(
			array(
				'tipo'    => 'box',
				'produto' => '',
				'preco'   => '',
				'loja'    => 'amazon',
				'url'     => '',
				'texto'   => 'Ver melhor preço',
				'slug'    => '',
				'nota'    => '',
				'pros'    => '',
				'contras' => '',
			),
			$atts,
			'affiliate_box'
		);
		$tipo = strtolower( trim( (string) $atts['tipo'] ) );
		if ( 'pros' === $tipo ) {
			return self::render_pros( $atts );
		}
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
		$go     = home_url( '/go/' . $link->slug );
		$botao  = sprintf(
			'<a class="cxaf-affiliate-btn" href="%s" target="_blank" rel="sponsored nofollow noopener">%s</a>',
			esc_url( $go ),
			esc_html( $atts['texto'] )
		);
		$produto = esc_html( $atts['produto'] );
		$loja    = esc_html( $atts['loja'] );
		$preco   = esc_html( $atts['preco'] );
		$nota    = esc_html( $atts['nota'] );
		if ( 'cta' === $tipo ) {
			return '<div class="cxaf-cta"><p class="cxaf-cta-texto">' . $produto
				. ( '' !== $preco ? ' — <strong>' . $preco . '</strong>' : '' )
				. '</p>' . $botao . '</div>';
		}
		$html = '<div class="cxaf-box"><div class="cxaf-box-info">';
		if ( '' !== $produto ) {
			$html .= '<strong class="cxaf-box-produto">' . $produto . '</strong>';
		}
		if ( '' !== $nota ) {
			$html .= '<span class="cxaf-box-nota">' . $nota . '</span>';
		}
		if ( '' !== $preco ) {
			$html .= '<span class="cxaf-box-preco">' . $preco . '</span>';
		}
		if ( '' !== $loja ) {
			$html .= '<span class="cxaf-box-loja">' . sprintf( 'na %s', $loja ) . '</span>';
		}
		return $html . '</div>' . $botao . '</div>';
	}

	protected static function render_pros( $atts ) {
		$para_lista = function ( $texto ) {
			$itens = array();
			foreach ( explode( ';', (string) $texto ) as $item ) {
				$item = trim( wp_strip_all_tags( $item ) );
				if ( '' !== $item ) {
					$itens[] = '<li>' . esc_html( $item ) . '</li>';
				}
			}
			return $itens;
		};
		$pros    = $para_lista( $atts['pros'] );
		$contras = $para_lista( $atts['contras'] );
		if ( ! $pros && ! $contras ) {
			return '';
		}
		$html = '<div class="cxaf-pros-contras"><div class="cxaf-pros"><strong>Prós</strong><ul>'
			. implode( '', $pros ) . '</ul></div>'
			. '<div class="cxaf-contras"><strong>Contras</strong><ul>'
			. implode( '', $contras ) . '</ul></div></div>';
		return $html;
	}
}
