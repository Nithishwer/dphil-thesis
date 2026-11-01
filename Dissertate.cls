% -------------------------------------------------------------------
%  @LaTeX-class-file{
%     filename        = "Dissertate.cls",
%     version         = "2.0",
%     date            = "25 March 2014",
%     codetable       = "ISO/ASCII",
%     keywords        = "LaTeX, Dissertate",
%     supported       = "Send email to suchow@post.harvard.edu.",
%     docstring       = "Class for a dissertation."
% --------------------------------------------------------------------

\NeedsTeXFormat{LaTeX2e}
% Appearance adapted from Zhaoxi Xiong, arXiv:1906.02892 (2019).
% Source: https://arxiv.org/src/1906.02892
\ProvidesClass{Dissertate}[2014/03/25 v2.0 Dissertate Class]
\LoadClass[12pt, twoside, openany, a4paper]{book}

%
% Options
%
\RequirePackage{etoolbox}

% Line spacing: dsingle/ddouble
%   Whether to use single- or doublespacing.
\newtoggle{DissertateSingleSpace}
\toggletrue{DissertateSingleSpace}
\DeclareOption{dsingle}{
    \toggletrue{DissertateSingleSpace}
    \ClassWarning{Dissertate}{Single-spaced mode on.}
}
\DeclareOption{ddouble}{\togglefalse{DissertateSingleSpace}}

\ProcessOptions\relax

% Line Spacing
%   Define two line spacings: one for the body, and one that is more compressed.
\iftoggle{DissertateSingleSpace}{
    \newcommand{\dnormalspacing}{1.2}
    \newcommand{\dcompressedspacing}{1.0}
}{
    \newcommand{\dnormalspacing}{2.0}
    \newcommand{\dcompressedspacing}{1.0}
}

\RequirePackage{setspace}

% Block quote with compressed spacing
\let\oldquote\quote
\let\endoldquote\endquote
\renewenvironment{quote}
    {\begin{spacing}{\dcompressedspacing}\oldquote}
    {\endoldquote\end{spacing}}

\RequirePackage{enumerate}

% Vertical layout measured from Tim Hempel's A4 dissertation.
\RequirePackage[
    a4paper,
    % Mirrored margins reserve binding space and keep each left edge at 3--3.5 cm.
    inner=35mm,
    outer=30mm,
    top=36.34mm,
    bottom=52.4mm,
    headheight=15pt,
    headsep=18.9pt,
    footskip=41.45pt
]{geometry}
\flushbottom
% Let paragraph gaps absorb the small adjustment to the shared bottom edge.
\setlength{\parskip}{0pt plus 3pt}
\usepackage{ragged2e}
\RaggedRight
\RequirePackage{graphicx}
\parindent 12pt
% Allow a final line-breaking pass for the sample's long Latin paragraphs.
\setlength{\emergencystretch}{1em}
\RequirePackage{lettrine}
\RequirePackage{verbatim}
\RequirePackage{pdfpages}

% Fonts.
\RequirePackage[T1]{fontenc}
\RequirePackage{lmodern}
\RequirePackage{color}
\RequirePackage{xcolor}
\usepackage{hyperref}
\RequirePackage{url}
\RequirePackage{amsfonts}
\RequirePackage{amssymb}
\RequirePackage{amsmath}
\RequirePackage{amsthm}
\RequirePackage{mathrsfs} % so that we can use \mathscr
\RequirePackage{amscd} % for the CD environment
\RequirePackage{mathtools}
\RequirePackage[labelfont={bf,rm,small,stretch=\dnormalspacing},
                textfont={rm,small,stretch=\dnormalspacing},
                labelsep=colon,
                justification=RaggedRight,
                singlelinecheck=false,
                margin=0pt,
                figurewithin=chapter,
                tablewithin=chapter]{caption}

% School color found from university's graphic identity site:
% http://isites.harvard.edu/icb/icb.do?keyword=k75408&pageid=icb.page392732
\definecolor{SchoolColor}{rgb}{0.6471, 0.1098, 0.1882} % Crimson

% Headings and headers.
\RequirePackage{fancyhdr}
\RequirePackage{titlesec}
\pagestyle{plain}
\RequirePackage{titling}

% Running headers and outer page numbers, following Tim Hempel's thesis.
\renewcommand{\chaptermark}[1]{\markboth{\@chapapp~\thechapter}{#1}}
\renewcommand{\sectionmark}[1]{}
\newcommand{\thesispagestyle}{
    \pagestyle{fancy}
    \fancyhf{}
    \fancyhead[LE]{\fontsize{9}{11}\selectfont\nouppercase{\leftmark}}
    \fancyhead[RO]{\fontsize{9}{11}\selectfont\nouppercase{\rightmark}}
    \fancyfoot[LE,RO]{%
        \parbox[b]{0.1\textwidth}{%
            \fontsize{9}{11}\selectfont
            \ifodd\value{page}\raggedleft\else\raggedright\fi
            \rule{\linewidth}{2pt}\\[3pt]
            \thepage
        }%
    }
    \renewcommand{\headrulewidth}{0pt}
    \renewcommand{\footrulewidth}{0pt}
    % Chapter openings retain the footer but omit the running header.
    \fancypagestyle{plain}{\fancyhead{}}
}

\setcounter{secnumdepth}{3}
\titleformat{\section}
    {\normalfont\rmfamily\Large\bfseries\raggedright}
    {\thesection}{1em}{}
\titleformat{\subsection}
    {\normalfont\rmfamily\large\bfseries\raggedright}
    {\thesubsection}{1em}{}
\titleformat{\subsubsection}
    {\normalfont\rmfamily\normalsize\bfseries\raggedright}
    {\thesubsubsection}{1em}{}
\titleformat*{\paragraph}
    {\normalfont\rmfamily\small\bfseries}
\titleformat*{\subparagraph}
    {\normalfont\rmfamily\small\bfseries}

% Chapter headings
\RequirePackage[palatino,nogrey]{quotchap}
\renewcommand*{\chapterheadstartvskip}{\vspace*{-0.5\baselineskip}}
\renewcommand*{\chapterheadendvskip}{\vspace{1.3\baselineskip}}
\definecolor{chaptergrey}{rgb}{0.6471, 0.1098, 0.1882} % for chapter numbers

% Counting
\RequirePackage{chngcntr}
\counterwithout{footnote}{chapter}

% Front matter.
\setcounter{tocdepth}{2}
\usepackage[titles]{tocloft}
\usepackage[titletoc]{appendix}
\renewcommand{\cftsecleader}{\cftdotfill{\cftdotsep}}
\renewcommand\listfigurename{List of figures}
\renewcommand\listtablename{List of tables}
\setlength\cftbeforechapskip{0pt}
\setlength\cftbeforesecskip{0pt}
\setlength\cftbeforesubsecskip{0pt}
\setlength\cftbeforesubsubsecskip{0pt}
\setlength\cftbeforefigskip{0pt}
\setlength\cftbeforetabskip{0pt}
% Keep contents entries upright and bold, as rendered in the reference.
\renewcommand\cftchapfont{\normalsize \bfseries}
\renewcommand\cftsecfont{\normalsize}
\renewcommand\cftsubsecfont{\normalsize}
\renewcommand\cftsubsubsecfont{\normalsize}
\renewcommand\cftfigfont{\normalsize}
\renewcommand\cfttabfont{\normalsize}

% Endmatter
\renewcommand{\setthesection}{\arabic{chapter}.A\arabic{section}}

% References.
\renewcommand\bibname{References}
\RequirePackage[square,comma,numbers,sort&compress]{natbib}
\renewcommand{\bibnumfmt}[1]{[#1]}

% An environment for paragraph-style section.
\providecommand\newthought[1]{%
   \addvspace{1.0\baselineskip plus 0.5ex minus 0.2ex}%
   \noindent\textsc{#1}%
}

% Align reference numbers so that they do not cause an indent.
\newlength\mybibindent
\setlength\mybibindent{0pt}
\renewenvironment{thebibliography}[1]
    {\chapter*{\bibname}%
     \@mkboth{\bibname}{\bibname}%
     \list{\@biblabel{\@arabic\c@enumiv}}
          {\settowidth\labelwidth{\@biblabel{999}}
           \leftmargin\labelwidth
            \advance\leftmargin\dimexpr\labelsep+\mybibindent\relax\itemindent-\mybibindent
           \@openbib@code
           \usecounter{enumiv}
           \let\p@enumiv\@empty
           \renewcommand\theenumiv{\@arabic\c@enumiv}}
     \sloppy
     \clubpenalty4000
     \@clubpenalty \clubpenalty
     \widowpenalty4000%
     \sfcode`\.\@m}
    {\def\@noitemerr
      {\@latex@warning{Empty `thebibliography' environment}}
     \endlist}

% Float environment options
\RequirePackage{float}

% Some definitions.
\def\advisor#1{\gdef\@advisor{#1}}
\def\coadvisorOne#1{\gdef\@coadvisorOne{#1}}
\def\coadvisorTwo#1{\gdef\@coadvisorTwo{#1}}
\def\committeeInternal#1{\gdef\@committeeInternal{#1}}
\def\committeeInternalOne#1{\gdef\@committeeInternalOne{#1}}
\def\committeeInternalTwo#1{\gdef\@committeeInternalTwo{#1}}
\def\committeeExternal#1{\gdef\@committeeExternal{#1}}
\def\degreeyear#1{\gdef\@degreeyear{#1}}
\def\degreemonth#1{\gdef\@degreemonth{#1}}
\def\degreeterm#1{\gdef\@degreeterm{#1}}
\def\degree#1{\gdef\@degree{#1}}
\def\department#1{\gdef\@department{#1}}
\def\field#1{\gdef\@field{#1}}
\def\university#1{\gdef\@university{#1}}
\def\universitycity#1{\gdef\@universitycity{#1}}
\def\universitystate#1{\gdef\@universitystate{#1}}
\def\programname#1{\gdef\@programname{#1}}
\def\pdOneName#1{\gdef\@pdOneName{#1}}
\def\pdOneSchool#1{\gdef\@pdOneSchool{#1}}
\def\pdOneYear#1{\gdef\@pdOneYear{#1}}
\def\pdTwoName#1{\gdef\@pdTwoName{#1}}
\def\pdTwoSchool#1{\gdef\@pdTwoSchool{#1}}
\def\pdTwoYear#1{\gdef\@pdTwoYear{#1}}
% School name and location
\university{Harvard University}
\universitycity{Cambridge}
\universitystate{Massachusetts}

% Hyperlinks
\hypersetup{
    colorlinks,
    citecolor=SchoolColor,
    filecolor=black,
    linkcolor=black,
    urlcolor=SchoolColor
}

% Formatting guidelines found in:
% http://www.gsas.harvard.edu/publications/form_of_the_phd_dissertation.php
\renewcommand{\frontmatter}{
    \input{frontmatter/personalize}
    \maketitle
    \copyrightpage
    \abstractpage
    \contentspage
    \begin{spacing}{\dnormalspacing}
   \listoftables
   \listoffigures % optional
   \end{spacing}
    \previousworks
    %\dedicationpage
    \acknowledgments
}

\renewcommand{\maketitle}{
    \pagenumbering{roman}
    \setcounter{page}{1}
    \thispagestyle{empty}
    \vspace*{\fill}
    % Match the title page's measured vertical position in the published PDF.
    \vspace{111.721pt}
    \begin{center}
    \begin{spacing}{2.0}
        \Huge \textcolor{SchoolColor}{\thetitle} \normalsize \\
    \end{spacing}
    \vspace{100pt}
    \textsc{a dissertation presented \\ by\\
    \theauthor\\ to\\ The Department of \@department\\
    \vspace{12pt}
    in partial fulfillment of the requirements\\
    for the degree of\\ \@degree\\
    in the subject of\\ \@field\\
    \vspace{12pt}
    \@university\\ \@universitycity, \@universitystate\\
    \@degreemonth\ \@degreeyear}
    \end{center} \vspace*{\fill}
}

\newcommand{\copyrightpage}{
    \newpage
    \thispagestyle{empty}
    \vspace*{\fill}
    {\scshape \small
    \noindent {\normalfont\copyright} ~ \@degreeyear\hspace{3pt} \theauthor \\
    \noindent all rights reserved.\par}
    \vspace*{\fill}
    \newpage
    \rm
}

\newcommand{\abstractpage}{
    \pdfbookmark{Abstract}{Abstract}
    \newpage
    \pagenumbering{roman}
    \setcounter{page}{3}
    \pagestyle{fancy}
    \lhead{Dissertation Advisor: Professor \@advisor} \rhead{\@author}
    \renewcommand{\headrulewidth}{0.0pt}
    \vspace*{35pt}
    \begin{center}
        \Large \textcolor{SchoolColor}{\@title} \normalsize \\
        \vspace*{20pt}
        \scshape Abstract \\ \rm
    \end{center}
    \begin{spacing}{\dnormalspacing}
        \input{frontmatter/abstract}
    \end{spacing}
    \vspace*{\fill}
    \newpage \lhead{} \rhead{}
    \cfoot{\thepage}
}

\newcommand{\contentspage}{
    \pdfbookmark{\contentsname}{Contents}
   \begin{spacing}{\dnormalspacing}
    \tableofcontents
    \end{spacing}
}

\newcommand{\previousworks}{
    \chapter*{Citations to previously published work}
    \noindent
    \begin{spacing}{\dnormalspacing}
        \input{frontmatter/previousworks}
    \end{spacing}
    \vspace*{\fill} \newpage
}

\newcommand{\dedicationpage}{
    \cleardoublepage
    \phantomsection
    \pdfbookmark{Dedication}{Dedication}
    \newpage \thispagestyle{fancy} \vspace*{\fill}
    \scshape \noindent \input{frontmatter/dedication}
    \vspace*{\fill} \newpage \rm
    \cleardoublepage
}

\newcommand{\acknowledgments}{
    \chapter*{Acknowledgments}
    \noindent
    \begin{spacing}{\dnormalspacing}
        \input{frontmatter/thanks}
    \end{spacing}
    \vspace*{\fill} \newpage
    \setcounter{page}{1}
    \pagenumbering{arabic}
}


\renewcommand{\backmatter}{
    \clearpage
    \addcontentsline{toc}{chapter}{References}
    \bibliographystyle{unsrt}
    \begin{spacing}{\dcompressedspacing}
        \bibliography{references}
    \end{spacing}
}
