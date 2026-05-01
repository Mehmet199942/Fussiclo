import os
import re

# The new footer HTML structure
NEW_FOOTER = """
	<footer class="main-footer">
		<div class="container">
			<img src="images/icons/logo-new.png" alt="LOGO" class="footer-logo">

			<div class="footer-newsletter">
				<h4>SIGN UP TO OUR NEWSLETTER</h4>
				<form class="footer-newsletter-form">
					<div class="footer-input-wrap">
						<input type="email" name="email" placeholder="Enter your email">
					</div>
					<button type="submit" class="footer-btn">ANMELDEN</button>
				</form>
			</div>

			<div class="footer-socials">
				<a href="#"><i class="zmdi zmdi-instagram"></i></a>
				<a href="#"><i class="zmdi zmdi-tiktok"></i></a>
				<a href="#"><i class="zmdi zmdi-whatsapp"></i></a>
			</div>

			<div class="footer-bottom">
				<div class="footer-meta">
					<div class="footer-meta-left">
						© FUSSI 2026
					</div>
					<div class="footer-bottom-links">
						<a href="support.html">Support</a>
						<a href="versand.html">Versandkonditionen</a>
						<a href="agb.html">AGB</a>
						<a href="impressum.html">Impressum</a>
						<a href="datenschutz.html">Datenschutzerklärung</a>
						<a href="cookie-einstellungen.html">Cookie-Einstellungen</a>
						<a href="jobs.html">Jobs</a>
					</div>
					<div class="footer-meta-right">
						<span><i class="zmdi zmdi-globe"></i> Deutsch</span>
						<span>€ EUR</span>
					</div>
				</div>
			</div>
		</div>
	</footer>
"""

def update_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # The goal is to replace ANY AND ALL footer blocks (including my newly added ones)
    # with a single instance of the NEW_FOOTER.
    
    # This pattern matches any comment-marker followed by a footer tag,
    # or just a footer tag.
    footer_pattern = re.compile(r'(<!--.*?Footer -->\s*)?<footer.*?</footer>', re.DOTALL)
    
    matches = list(footer_pattern.finditer(content))
    
    if not matches:
        return False

    # If we have multiple footers, we want to replace the entire range from the first to the last
    # IF they are relatively close to each other (at the bottom of the file).
    # But for safety in this project, we can usually just replace all occurrences
    # and then if we ended up with duplicates, we'll strip them in a second pass or just replace carefully.
    
    # Better approach: Replace the FIRST one with the NEW_FOOTER and DELETE the rest.
    
    new_content = content
    # Work from back to front to avoid index shifts
    for i in range(len(matches) - 1, 0, -1):
        m = matches[i]
        new_content = new_content[:m.start()] + new_content[m.end():]
        
    # Now replace the first one
    m0 = matches[0]
    # Re-calculate index since we've deleted things after it (but start index of first match doesn't change)
    new_content = new_content[:m0.start()] + '<!-- Redesigned Footer -->\n' + NEW_FOOTER + new_content[m0.end():]

    if new_content != content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        return True
    return False

def main():
    root_dir = r'c:\Users\mehme\Desktop\cozastore-master'
    count = 0
    for root, dirs, files in os.walk(root_dir):
        if 'node_modules' in dirs:
            dirs.remove('node_modules')
        if '.git' in dirs:
            dirs.remove('.git')
            
        for file in files:
            if file.endswith('.html'):
                filepath = os.path.join(root, file)
                if update_file(filepath):
                    print(f"Updated: {filepath}")
                    count += 1
    print(f"Total files updated: {count}")

if __name__ == "__main__":
    main()
