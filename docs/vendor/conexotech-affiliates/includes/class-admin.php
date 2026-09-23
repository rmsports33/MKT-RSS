<?php
/**
 * CXAF_Admin — menu "Afiliados": painel + cadastro de links.
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

class CXAF_Admin {

	public static function init() {
		add_action( 'admin_menu', array( __CLASS__, 'menu' ) );
	}

	public static function menu() {
		add_menu_page(
			'Afiliados',
			'Afiliados',
			'manage_options',
			'cxaf-dashboard',
			array( __CLASS__, 'render_dashboard' ),
			'dashicons-chart-line',
			58
		);
		add_submenu_page(
			'cxaf-dashboard',
			'Links de afiliado',
			'Links',
			'manage_options',
			'cxaf-links',
			array( __CLASS__, 'render_links' )
		);
	}

	public static function render_dashboard() {
		if ( ! current_user_can( 'manage_options' ) ) {
			wp_die( 'Sem permissão.' );
		}
		$total_7  = CXAF_DB::count_clicks( 7 );
		$total_30 = CXAF_DB::count_clicks( 30 );
		$by_day   = CXAF_DB::clicks_by_day( 14 );
		$top      = CXAF_DB::top_links( 30, 10 );
		$recent   = CXAF_DB::recent_clicks( 20 );
		?>
		<div class="wrap">
			<h1>Afiliados — rastreio nativo</h1>
			<?php if ( isset( $_GET['cxaf_checked'] ) ) : ?>
				<div class="notice notice-success"><p><?php printf( 'Verificação concluída: %d links checados.', absint( $_GET['cxaf_checked'] ) ); ?></p></div>
			<?php endif; ?>
			<p>Os cliques passam pelo redirecionador <code>/go/{slug}</code> e são gravados neste painel. Sem serviço externo.</p>
			<h2>Totais</h2>
			<table class="widefat striped" style="max-width:520px">
				<tbody>
					<tr><th scope="row">Cliques (7 dias)</th><td><?php echo esc_html( $total_7 ); ?></td></tr>
					<tr><th scope="row">Cliques (30 dias)</th><td><?php echo esc_html( $total_30 ); ?></td></tr>
				</tbody>
			</table>
			<h2>Saúde dos links</h2>
			<p><a class="button" href="<?php echo esc_url( wp_nonce_url( admin_url( 'admin-post.php?action=cxaf_check_now' ), 'cxaf_check_now' ) ); ?>">Verificar agora</a> <span class="description">Checa até 30 links por vez. O cron diário verifica 50 por dia.</span></p>
			<table class="widefat striped">
				<thead><tr><th scope="col">Slug</th><th scope="col">Produto</th><th scope="col">Loja</th><th scope="col">Código</th><th scope="col">Mensagem</th><th scope="col">Verificado em</th></tr></thead>
				<tbody>
				<?php $broken = CXAF_DB::broken_links( 20 ); ?>
				<?php if ( $broken ) : ?>
					<?php foreach ( $broken as $b ) : ?>
					<tr>
						<td><code><?php echo esc_html( $b->slug ); ?></code></td>
						<td><?php echo esc_html( $b->produto ); ?></td>
						<td><?php echo esc_html( $b->loja ); ?></td>
						<td><?php echo esc_html( $b->status_code ); ?></td>
						<td><?php echo esc_html( $b->status_msg ); ?></td>
						<td><?php echo esc_html( $b->verificado_em ); ?></td>
					</tr>
					<?php endforeach; ?>
				<?php else : ?>
					<tr><td colspan="6">Nenhum link quebrado. Verificação diária ativa.</td></tr>
				<?php endif; ?>
				</tbody>
			</table>
			<h2>Cliques por dia (14 dias)</h2>
			<table class="widefat striped" style="max-width:520px">
				<thead><tr><th scope="col">Dia</th><th scope="col">Cliques</th></tr></thead>
				<tbody>
				<?php if ( $by_day ) : ?>
					<?php foreach ( $by_day as $row ) : ?>
					<tr><td><?php echo esc_html( $row->dia ); ?></td><td><?php echo esc_html( $row->total ); ?></td></tr>
					<?php endforeach; ?>
				<?php else : ?>
					<tr><td colspan="2">Nenhum clique registrado ainda.</td></tr>
				<?php endif; ?>
				</tbody>
			</table>
			<h2>Links mais clicados (30 dias)</h2>
			<table class="widefat striped">
				<thead><tr><th scope="col">Slug</th><th scope="col">Produto</th><th scope="col">Loja</th><th scope="col">Cliques</th></tr></thead>
				<tbody>
				<?php if ( $top ) : ?>
					<?php foreach ( $top as $row ) : ?>
					<tr>
						<td><code><?php echo esc_html( $row->slug ); ?></code></td>
						<td><?php echo esc_html( $row->produto ); ?></td>
						<td><?php echo esc_html( $row->loja ); ?></td>
						<td><?php echo esc_html( $row->total ); ?></td>
					</tr>
					<?php endforeach; ?>
				<?php else : ?>
					<tr><td colspan="4">Nenhum clique registrado ainda.</td></tr>
				<?php endif; ?>
				</tbody>
			</table>
			<h2>Cliques recentes</h2>
			<table class="widefat striped">
				<thead><tr><th scope="col">Data</th><th scope="col">Slug</th><th scope="col">Produto</th><th scope="col">Loja</th><th scope="col">Origem</th></tr></thead>
				<tbody>
				<?php if ( $recent ) : ?>
					<?php foreach ( $recent as $row ) : ?>
					<tr>
						<td><?php echo esc_html( $row->criado_em ); ?></td>
						<td><code><?php echo esc_html( $row->slug ); ?></code></td>
						<td><?php echo esc_html( $row->produto ); ?></td>
						<td><?php echo esc_html( $row->loja ); ?></td>
						<td><?php echo $row->referrer ? esc_html( wp_parse_url( $row->referrer, PHP_URL_HOST ) ) : '—'; ?></td>
					</tr>
					<?php endforeach; ?>
				<?php else : ?>
					<tr><td colspan="5">Nenhum clique registrado ainda.</td></tr>
				<?php endif; ?>
				</tbody>
			</table>
		</div>
		<?php
	}

	public static function render_links() {
		if ( ! current_user_can( 'manage_options' ) ) {
			wp_die( 'Sem permissão.' );
		}
		$notice = '';
		if ( isset( $_POST['cxaf_add_link'] ) ) {
			check_admin_referer( 'cxaf_add_link' );
			$slug    = isset( $_POST['slug'] ) ? sanitize_title( wp_unslash( $_POST['slug'] ) ) : '';
			$url     = isset( $_POST['url'] ) ? esc_url_raw( trim( wp_unslash( $_POST['url'] ) ) ) : '';
			$loja    = isset( $_POST['loja'] ) ? sanitize_text_field( wp_unslash( $_POST['loja'] ) ) : '';
			$produto = isset( $_POST['produto'] ) ? sanitize_text_field( wp_unslash( $_POST['produto'] ) ) : '';
			if ( '' === $slug || '' === $url ) {
				$notice = 'Informe slug e URL válida.';
			} elseif ( CXAF_DB::get_or_create_link( $slug, $url, $loja, $produto, 0 ) ) {
				$notice = 'Link salvo: /go/' . $slug;
			} else {
				$notice = 'Não foi possível salvar. Verifique o slug e a URL.';
			}
		}
		$links = CXAF_DB::all_links( 200 );
		?>
		<div class="wrap">
			<h1>Links de afiliado</h1>
			<?php if ( $notice ) : ?>
				<div class="notice notice-info"><p><?php echo esc_html( $notice ); ?></p></div>
			<?php endif; ?>
			<h2>Adicionar link</h2>
			<form method="post" action="">
				<?php wp_nonce_field( 'cxaf_add_link' ); ?>
				<table class="form-table">
					<tr><th scope="row"><label for="cxaf-slug">Slug</label></th><td><input id="cxaf-slug" name="slug" type="text" class="regular-text" placeholder="ex.: galaxy-s24-amazon" required></td></tr>
					<tr><th scope="row"><label for="cxaf-url">URL afiliada</label></th><td><input id="cxaf-url" name="url" type="url" class="regular-text" placeholder="https://..." required></td></tr>
					<tr><th scope="row"><label for="cxaf-loja">Loja</label></th><td><input id="cxaf-loja" name="loja" type="text" class="regular-text" placeholder="amazon"></td></tr>
					<tr><th scope="row"><label for="cxaf-produto">Produto</label></th><td><input id="cxaf-produto" name="produto" type="text" class="regular-text" placeholder="Galaxy S24"></td></tr>
				</table>
				<p><input type="submit" name="cxaf_add_link" class="button button-primary" value="Salvar link"></p>
			</form>
			<h2>Links cadastrados</h2>
			<table class="widefat striped">
				<thead><tr><th scope="col">URL curta</th><th scope="col">Produto</th><th scope="col">Loja</th><th scope="col">Status</th><th scope="col">Destino</th></tr></thead>
				<tbody>
				<?php if ( $links ) : ?>
					<?php foreach ( $links as $link ) : ?>
					<tr>
						<td><code><?php echo esc_html( home_url( '/go/' . $link->slug ) ); ?></code></td>
						<td><?php echo esc_html( $link->produto ); ?></td>
						<td><?php echo esc_html( $link->loja ); ?></td>
						<td><?php echo ( isset( $link->verificado_em ) && '0000-00-00 00:00:00' !== $link->verificado_em ) ? esc_html( $link->status_code . ' — ' . $link->status_msg ) : '—'; ?></td>
						<td><?php echo esc_html( mb_strimwidth( $link->url, 0, 80, '…' ) ); ?></td>
					</tr>
					<?php endforeach; ?>
				<?php else : ?>
					<tr><td colspan="5">Nenhum link cadastrado ainda.</td></tr>
				<?php endif; ?>
				</tbody>
			</table>
		</div>
		<?php
	}
}
