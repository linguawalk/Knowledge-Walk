# KnowledgeWalk Core 0.1.0

Initial WordPress plugin for the KnowledgeWalk encyclopedia.

## Features
- Custom post type `kw_article` (`/encyclopedia/<slug>/`)
- Hierarchical taxonomy `kw_topic` (`/topics/<parent>/<child>/`)
- WordPress block editor and REST API enabled
- Rewrite rules flushed only on activation/deactivation

## Install
1. Back up the WordPress site and database.
2. Test on a staging site if available.
3. Upload `knowledgewalk-core.zip` via WordPress Admin > Plugins > Add Plugin > Upload Plugin.
4. Activate **KnowledgeWalk Core**.
5. Add topics manually under **백과사전 문서 > 지식 분류**.
6. Add a draft under **백과사전 문서 > 새 글 추가** and verify its preview.

This initial version does not create the seven root topics automatically, modify existing posts, or add AI publishing.
